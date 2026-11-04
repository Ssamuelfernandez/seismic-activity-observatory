"""Pruebas de common/logging_setup.py: el aviso se conserva y el traceback se descarta."""
import logging

from common.logging_setup import DropTracebackFilter


def test_filter_drops_traceback_but_keeps_the_record():
    try:
        raise ConnectionError("sin base")
    except ConnectionError:
        import sys
        record = logging.LogRecord("asyncpg.pool", logging.WARNING, __file__, 1, "aviso", None, sys.exc_info())
    assert record.exc_info is not None
    assert DropTracebackFilter().filter(record) is True
    assert record.exc_info is None
    assert record.getMessage() == "aviso"
