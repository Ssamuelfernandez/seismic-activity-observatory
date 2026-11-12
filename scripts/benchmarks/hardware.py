"""Equipo leído de la máquina que ejecuta las mediciones (K2, FR-010). Sin `psutil`.

Lo que se ve desde el contenedor es la VM de Docker Desktop, no el PC anfitrión: por eso el
modelo de equipo y su potencia quedan «PENDIENTE (alumno)». Lo que no se puede leer se
declara «no disponible»; nunca se inventa.
"""
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.benchmarks.labels import PENDING_STUDENT, UNAVAILABLE

KIB_PER_GIB = 1024 * 1024
CGROUP_UNLIMITED = "max"


@dataclass(frozen=True)
class CpuInfo:
    """CPU leída de `/proc/cpuinfo`: modelo y núcleos (None = no disponible)."""

    model: str | None
    logical: int | None
    physical: int | None


@dataclass(frozen=True)
class MachineInfo:
    """Todo lo que `equipo.md` informa de la máquina de medición."""

    cpu: CpuInfo
    ram_kib: int | None
    os_name: str
    python_version: str
    postgres_version: str | None
    shapely_version: str | None
    cpu_limit: str | None
    memory_limit: str | None


def parse_cpuinfo(text: str) -> CpuInfo:
    """Extrae modelo, núcleos lógicos y físicos del texto de `/proc/cpuinfo`.

    Qué hace:
        Toma el primer `model name`, cuenta las líneas `processor` y los pares únicos
        (`physical id`, `core id`) como núcleos físicos.
    Recibe:
        text: contenido de `/proc/cpuinfo` (vacío si no existe).
    Devuelve:
        `CpuInfo`; cada campo que no aparece es None.
    Por qué existe:
        Documenta el equipo sin depender de `psutil` (K2, FR-010).
    """
    model = re.search(r"^model name\s*:\s*(.+)$", text, re.MULTILINE)
    logical = len(re.findall(r"^processor\s*:", text, re.MULTILINE)) or None
    cores = set()
    for block in text.split("\n\n"):
        physical_id = re.search(r"^physical id\s*:\s*(\d+)", block, re.MULTILINE)
        core_id = re.search(r"^core id\s*:\s*(\d+)", block, re.MULTILINE)
        if physical_id and core_id:
            cores.add((physical_id.group(1), core_id.group(1)))
    return CpuInfo(model.group(1).strip() if model else None, logical, len(cores) or None)


def parse_meminfo(text: str) -> int | None:
    """Devuelve `MemTotal` de `/proc/meminfo` en KiB, o None si no aparece."""
    match = re.search(r"^MemTotal:\s*(\d+)\s*kB", text, re.MULTILINE)
    return int(match.group(1)) if match else None


def parse_cgroup_limits(cpu_max: str, memory_max: str) -> tuple[str | None, str | None]:
    """Interpreta `cpu.max` y `memory.max` de cgroup v2; `max` significa sin límite."""
    cpu = None
    parts = cpu_max.split()
    if len(parts) == 2 and parts[0] != CGROUP_UNLIMITED and parts[1].isdigit() and int(parts[1]) > 0:
        cpu = f"{int(parts[0]) / int(parts[1]):.2f} CPU"
    memory_text = memory_max.strip()
    memory = None
    if memory_text.isdigit():
        memory = f"{int(memory_text) / (KIB_PER_GIB * 1024):.2f} GiB"
    return cpu, memory


def _read_text(path: Path) -> str:
    """Lee un archivo de texto; devuelve cadena vacía si no existe o no se puede leer."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _shapely_version() -> str | None:
    """Versión instalada de `shapely`, o None si no está."""
    try:
        import shapely
    except ImportError:
        return None
    return shapely.__version__


def read_machine(proc_dir: Path = Path("/proc"), cgroup_dir: Path = Path("/sys/fs/cgroup"),
                 postgres_version: str | None = None) -> MachineInfo:
    """Lee el equipo de la máquina que ejecuta las mediciones.

    Recibe:
        proc_dir, cgroup_dir: raíces de `/proc` y de cgroup (inyectables en las pruebas);
        postgres_version: resultado de `SELECT version()`, que lee quien tiene la conexión.
    Devuelve:
        `MachineInfo` con None en lo que no se pudo leer.
    Por qué existe:
        FR-010 pide el equipo medido, no tecleado a mano (K2, SC-002).
    """
    cpu = parse_cpuinfo(_read_text(proc_dir / "cpuinfo"))
    if cpu.logical is None and cpu.model is None:
        cpu = CpuInfo(None, os.cpu_count(), None)
    cpu_limit, memory_limit = parse_cgroup_limits(_read_text(cgroup_dir / "cpu.max"),
                                                  _read_text(cgroup_dir / "memory.max"))
    return MachineInfo(cpu, parse_meminfo(_read_text(proc_dir / "meminfo")),
                       platform.platform(), platform.python_version(), postgres_version,
                       _shapely_version(), cpu_limit, memory_limit)


def _or_unavailable(value: object) -> str:
    """Texto de un campo opcional: el valor o «no disponible»."""
    return UNAVAILABLE if value is None else str(value)


def render_equipo_md(info: MachineInfo) -> str:
    """Genera el contenido de `equipo.md` con el equipo medido y los campos del alumno.

    Recibe:
        info: resultado de `read_machine`.
    Devuelve:
        Texto Markdown con CPU, núcleos, RAM, SO, versiones y límites del contenedor, y el
        modelo del equipo anfitrión y su potencia como «PENDIENTE (alumno)».
    Por qué existe:
        Sin el equipo, las cifras de tiempo no se pueden interpretar (K2, FR-010, SC-002).
    """
    ram = UNAVAILABLE if info.ram_kib is None else f"{info.ram_kib / KIB_PER_GIB:.2f} GiB"
    rows = [
        ("Modelo de CPU", _or_unavailable(info.cpu.model)),
        ("Núcleos físicos", _or_unavailable(info.cpu.physical)),
        ("Núcleos lógicos", _or_unavailable(info.cpu.logical)),
        ("RAM total", ram),
        ("Sistema operativo", info.os_name),
        ("Python", info.python_version),
        ("PostgreSQL", _or_unavailable(info.postgres_version)),
        ("shapely", _or_unavailable(info.shapely_version)),
        ("Límite de CPU del contenedor", _or_unavailable(info.cpu_limit)),
        ("Límite de memoria del contenedor", _or_unavailable(info.memory_limit)),
        ("Modelo del equipo anfitrión", PENDING_STUDENT),
        ("Potencia del equipo anfitrión (W)", PENDING_STUDENT),
    ]
    lines = ["# Equipo de medición", "",
             "Leído de la máquina que ejecuta las mediciones: es la VM de Docker Desktop, no el PC "
             "anfitrión (límite conocido). Los campos del anfitrión los aporta el alumno.", "",
             "| Campo | Valor |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in rows]
    return "\n".join(lines) + "\n"
