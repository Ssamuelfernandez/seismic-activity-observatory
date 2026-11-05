"""Pruebas del arranque de la carga: argumentos y ayuda (T013); la carga real va en integración."""
from pathlib import Path

from historical.load_main import DEFAULT_INPUT_DIR, build_parser


def test_input_dir_defaults_to_data_historical() -> None:
    assert build_parser().parse_args([]).input_dir == Path(DEFAULT_INPUT_DIR)


def test_input_dir_can_be_changed() -> None:
    assert build_parser().parse_args(["--input-dir", "otra"]).input_dir == Path("otra")
