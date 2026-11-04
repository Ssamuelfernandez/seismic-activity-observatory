"""Pruebas de consumer/fault_hook.py: caída única tras el commit de PostgreSQL (T051, prueba 8)."""
import logging

from common.records import MessageRef
from consumer import fault_hook

TARGET = 3


def ref(offset: int) -> MessageRef:
    return MessageRef("earthquakes.live", 0, offset)


class ExitSpy:
    """Doble de `os._exit`: anota el código y no termina el proceso."""

    def __init__(self):
        self.codes: list[int] = []

    def __call__(self, code: int) -> None:
        self.codes.append(code)


def make_hook(tmp_path, spy: ExitSpy):
    marker = tmp_path / "fault_done"
    return fault_hook.crash_once_at_offset(TARGET, str(marker), spy), marker


def test_does_not_exit_at_another_offset(tmp_path):
    spy = ExitSpy()
    hook, marker = make_hook(tmp_path, spy)
    hook(ref(TARGET - 1), True)
    hook(ref(TARGET + 1), True)
    assert spy.codes == [] and not marker.exists()


def test_exits_with_137_at_the_chosen_offset_and_writes_the_marker(tmp_path):
    spy = ExitSpy()
    hook, marker = make_hook(tmp_path, spy)
    hook(ref(TARGET), True)
    assert spy.codes == [137] and marker.exists()


def test_warning_is_emitted_before_exiting(tmp_path, caplog):
    order: list[str] = []

    def exit_after_log(code: int) -> None:
        order.append("exit")

    class Spy(logging.Handler):
        def emit(self, record):
            order.append(record.getMessage())

    logger = logging.getLogger("consumer.fault_hook")
    handler = Spy()
    logger.addHandler(handler)
    try:
        with caplog.at_level(logging.WARNING, logger="consumer.fault_hook"):
            hook = fault_hook.crash_once_at_offset(TARGET, str(tmp_path / "m"), exit_after_log)
            hook(ref(TARGET), True)
    finally:
        logger.removeHandler(handler)
    assert order == [f"FAULT crash_after_db_commit offset={TARGET}", "exit"]
    assert caplog.records[0].levelno == logging.WARNING


def test_with_the_marker_present_it_does_nothing(tmp_path):
    spy = ExitSpy()
    hook, marker = make_hook(tmp_path, spy)
    marker.write_text("done")
    hook(ref(TARGET), True)
    assert spy.codes == []


def test_second_arrival_after_the_crash_does_not_die_again(tmp_path):
    spy = ExitSpy()
    hook, _ = make_hook(tmp_path, spy)
    hook(ref(TARGET), True)
    hook(ref(TARGET), True)
    assert spy.codes == [137]


def test_non_synthetic_message_never_triggers_nor_writes_the_marker(tmp_path):
    spy = ExitSpy()
    hook, marker = make_hook(tmp_path, spy)
    hook(ref(TARGET), False)
    assert spy.codes == [] and not marker.exists()


def test_build_fault_hook_returns_none_when_the_variable_is_empty():
    assert fault_hook.build_fault_hook(None) is None


def test_build_fault_hook_returns_a_callable_with_the_default_marker():
    hook = fault_hook.build_fault_hook(5)
    assert callable(hook)
    assert fault_hook.FAULT_MARKER_PATH == "/tmp/consumer_fault_done"
    assert fault_hook.FAULT_EXIT_CODE == 137
