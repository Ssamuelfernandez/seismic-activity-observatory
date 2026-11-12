"""Costes de K6 (puro): seis categorías con fórmula, etiqueta y entradas con origen (FR-018, FR-021, FR-022).

Nada se rellena por defecto: lo que solo conoce el alumno es `PENDING` y el resultado es
«no calculable» (nunca 0). Solo es MEDIDO lo que se mide (tamaños y bytes de transferencia).
"""
from collections.abc import Callable
from dataclasses import dataclass

from scripts.benchmarks.labels import NOT_COMPUTABLE, PENDING_STUDENT

MEASURED = "MEDIDO"
ASSUMED = "SUPUESTO"
BYTES_PER_GIB = 1024 ** 3
CATEGORIES = ("hardware", "electricidad", "almacenamiento", "transferencia", "mantenimiento", "horas de desarrollo")
FREE_QUOTA_NOTE = "cuota gratuita ≠ coste cero: superar el límite puede generar un cobro."
FREE_QUOTA_SERVICES = ("hosting estático (Netlify)", "túnel (Cloudflare Tunnel)", "otros servicios usados")


class _Pending:
    """Marca explícita de un dato que aporta el alumno (no es un número ni se rellena sola)."""

    def __repr__(self) -> str:
        return "PENDING"


PENDING = _Pending()


@dataclass(frozen=True)
class CostInput:
    """Entrada de un coste: nombre, valor o `PENDING`, origen (MEDIDO o SUPUESTO) y unidad."""

    name: str
    value: float | _Pending
    origin: str
    unit: str


@dataclass(frozen=True)
class CostRow:
    """Fila de coste: categoría, fórmula, entradas, unidad del resultado y cómo calcularlo."""

    category: str
    formula: str
    inputs: dict[str, CostInput]
    unit: str
    compute: Callable[[dict[str, float]], float]

    @property
    def label(self) -> str:
        """MEDIDO solo si todas las entradas lo son; si no, SUPUESTO."""
        return MEASURED if all(i.origin == MEASURED for i in self.inputs.values()) else ASSUMED

    def result(self) -> float | None:
        """Resultado por la fórmula, o `None` («no calculable») si alguna entrada es `PENDING`."""
        if any(isinstance(i.value, _Pending) for i in self.inputs.values()):
            return None
        return self.compute({name: i.value for name, i in self.inputs.items()})


def _pending(name: str, unit: str) -> CostInput:
    """Entrada que debe aportar el alumno."""
    return CostInput(name, PENDING, ASSUMED, unit)


def build_rows(storage_bytes: float | None = None, bytes_per_visit: float | None = None) -> list[CostRow]:
    """Las 6 filas de K6; los tamaños y bytes medidos se pasan como entrada, el resto queda `PENDING`.

    Recibe:
        storage_bytes: tamaño MEDIDO de la base (bytes); bytes_per_visit: bytes MEDIDOS de una visita.
    Devuelve:
        Seis `CostRow` en el orden de `CATEGORIES`; nada se rellena por defecto.
    Por qué existe:
        El coste se calcula con entradas con origen; lo desconocido no se inventa (FR-021, SC-005).
    """
    gib = PENDING if storage_bytes is None else storage_bytes / BYTES_PER_GIB
    visit_gib = PENDING if bytes_per_visit is None else bytes_per_visit / BYTES_PER_GIB
    return [
        CostRow("hardware", "precio / vida_útil_meses x fracción_de_uso",
                {"precio": _pending("precio", "EUR"), "vida_util": _pending("vida_util", "meses"),
                 "fraccion": _pending("fraccion", "0-1")}, "EUR/mes",
                lambda v: v["precio"] / v["vida_util"] * v["fraccion"]),
        CostRow("electricidad", "potencia_W / 1000 x horas_encendido_mes x EUR_por_kWh",
                {"potencia": _pending("potencia", "W"), "horas": _pending("horas", "h/mes"),
                 "tarifa": _pending("tarifa", "EUR/kWh")}, "EUR/mes",
                lambda v: v["potencia"] / 1000 * v["horas"] * v["tarifa"]),
        CostRow("almacenamiento", "GiB medidos x EUR_por_GiB_mes",
                {"gib": CostInput("gib", gib, MEASURED, "GiB (base 1024, `pg_database_size`)"),
                 "tarifa": _pending("tarifa", "EUR/GiB-mes")}, "EUR/mes", lambda v: v["gib"] * v["tarifa"]),
        CostRow("transferencia", "GiB por visita medidos x visitas_mes x EUR_por_GiB",
                {"gib_visita": CostInput("gib_visita", visit_gib, MEASURED, "GiB por visita"),
                 "visitas": _pending("visitas", "visitas/mes"), "tarifa": _pending("tarifa", "EUR/GiB")}, "EUR/mes",
                lambda v: v["gib_visita"] * v["visitas"] * v["tarifa"]),
        CostRow("mantenimiento", "horas_mes x EUR_por_hora",
                {"horas": _pending("horas", "h/mes"), "tarifa": _pending("tarifa", "EUR/h")}, "EUR/mes",
                lambda v: v["horas"] * v["tarifa"]),
        CostRow("horas de desarrollo", "horas_totales x EUR_por_hora",
                {"horas": _pending("horas", "h"), "tarifa": _pending("tarifa", "EUR/h")}, "EUR (una vez)",
                lambda v: v["horas"] * v["tarifa"]),
    ]


def _value(entry: CostInput) -> str:
    """Valor de una entrada: el número o «PENDIENTE (alumno)»."""
    return PENDING_STUDENT if isinstance(entry.value, _Pending) else f"{entry.value:g}"


def render_costs_md(rows: list[CostRow]) -> str:
    """Genera `costes.md`: una fila por categoría, entradas con origen y unidad, y la nota de cuotas gratuitas."""
    lines = ["# Costes (K6)", "",
             "MEDIDO solo lo que se mide (tamaños, bytes de transferencia). Todo lo demás es SUPUESTO y queda "
             f"como `{PENDING_STUDENT}`; mientras falte una entrada, el resultado es «{NOT_COMPUTABLE}» (nunca 0).", "",
             "| Categoría | Etiqueta | Fórmula | Entradas (valor; origen; unidad) | Resultado |", "|---|---|---|---|---|"]
    for row in rows:
        inputs = "<br>".join(f"{i.name} = {_value(i)}; {i.origin}; {i.unit}" for i in row.inputs.values())
        result = row.result()
        shown = NOT_COMPUTABLE if result is None else f"{result:.4f} {row.unit}"
        lines.append(f"| {row.category} | {row.label} | {row.formula} | {inputs} | {shown} |")
    lines += ["", "## Cuotas gratuitas (hosting estático, túnel y demás servicios)", "", FREE_QUOTA_NOTE, "",
              "| Servicio | Límite | Fecha de consulta | Consecuencia de superarlo |", "|---|---|---|---|"]
    lines += [f"| {service} | {PENDING_STUDENT} | {PENDING_STUDENT} | {PENDING_STUDENT} |"
              for service in FREE_QUOTA_SERVICES]
    return "\n".join(lines) + "\n"
