"""Pruebas sin Docker de la lectura del equipo (T075, K2, FR-010)."""
from pathlib import Path

from scripts.benchmarks.hardware import (parse_cgroup_limits, parse_cpuinfo, parse_meminfo, read_machine,
                                         render_equipo_md)
from scripts.benchmarks.labels import PENDING_STUDENT, UNAVAILABLE

CPUINFO = """processor\t: 0
model name\t: Intel(R) Core(TM) i7 de ejemplo
physical id\t: 0
core id\t\t: 0

processor\t: 1
model name\t: Intel(R) Core(TM) i7 de ejemplo
physical id\t: 0
core id\t\t: 0

processor\t: 2
model name\t: Intel(R) Core(TM) i7 de ejemplo
physical id\t: 0
core id\t\t: 1

processor\t: 3
model name\t: Intel(R) Core(TM) i7 de ejemplo
physical id\t: 0
core id\t\t: 1
"""
MEMINFO = "MemTotal:       16777216 kB\nMemFree:         1000 kB\n"


def test_parse_cpuinfo_reads_model_and_cores() -> None:
    cpu = parse_cpuinfo(CPUINFO)
    assert cpu.model == "Intel(R) Core(TM) i7 de ejemplo"
    assert (cpu.logical, cpu.physical) == (4, 2)


def test_parse_meminfo_and_cgroup_limits() -> None:
    assert parse_meminfo(MEMINFO) == 16777216
    assert parse_meminfo("") is None
    assert parse_cgroup_limits("max 100000", "max") == (None, None)
    assert parse_cgroup_limits("200000 100000", "2147483648") == ("2.00 CPU", "2.00 GiB")


def test_render_has_machine_fields_and_pending_host(tmp_path: Path) -> None:
    (tmp_path / "cpuinfo").write_text(CPUINFO, encoding="utf-8")
    (tmp_path / "meminfo").write_text(MEMINFO, encoding="utf-8")
    text = render_equipo_md(read_machine(tmp_path, tmp_path, "PostgreSQL 16.x de ejemplo"))
    for expected in ("i7 de ejemplo", "| Núcleos físicos | 2 |", "| Núcleos lógicos | 4 |", "16.00 GiB",
                     "PostgreSQL 16.x de ejemplo", "Sistema operativo"):
        assert expected in text
    assert f"| Modelo del equipo anfitrión | {PENDING_STUDENT} |" in text
    assert f"| Potencia del equipo anfitrión (W) | {PENDING_STUDENT} |" in text


def test_missing_proc_says_unavailable_without_inventing(tmp_path: Path) -> None:
    info = read_machine(tmp_path / "no-existe", tmp_path / "no-existe")
    text = render_equipo_md(info)
    assert info.cpu.model is None and info.ram_kib is None
    assert f"| Modelo de CPU | {UNAVAILABLE} |" in text
    assert f"| RAM total | {UNAVAILABLE} |" in text
    assert f"| PostgreSQL | {UNAVAILABLE} |" in text
