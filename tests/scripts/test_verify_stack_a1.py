"""Pruebas del reconocimiento de la línea de decisión que usa el check A1 de `verify_stack.py`."""
from scripts.verify_stack import is_synthetic_decision_line

LINE = "decision=new_event event_id=synthetic-1793821694 topic=earthquakes.live partition=0 offset=3"


def test_accepts_a_decision_on_a_synthetic_event():
    assert is_synthetic_decision_line(LINE)


def test_accepts_a_quarantine_decision_on_a_synthetic_event():
    assert is_synthetic_decision_line(LINE.replace("new_event", "quarantined") + " reason=x")


def test_rejects_other_events_and_non_decision_lines():
    assert not is_synthetic_decision_line(LINE.replace("synthetic-", "us"))
    assert not is_synthetic_decision_line("Evento recibido event_id=synthetic-1")
    assert not is_synthetic_decision_line("")
