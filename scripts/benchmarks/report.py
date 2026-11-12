"""Informes de las mediciones (puro): `resultados.json`, `tablas.md`, `indices.md` y `aislamiento.md`.

No mide ni toca la base: recibe los registros ya medidos y los convierte en texto. Todo lo que
sale de `bench` lleva la etiqueta SINTÉTICO y ninguna celda queda vacía (se escribe «no aplica»).
"""
from scripts.benchmarks.labels import SYNTHETIC_LABEL
from scripts.benchmarks.records import Measurement
from scripts.benchmarks.storage import RealReference, render_real_reference
from scripts.benchmarks.synth import RNG_SEED
from scripts.benchmarks.verdicts import Verdict, overall_verdict

NOT_APPLICABLE = "no aplica"
OPERATION_TITLES = {"search": "Operación a: búsqueda por id", "geo": "Operación b: integración geográfica",
                    "agg": "Operación c y E6: agregaciones Q4, Q3 y Q2 sin y con índice"}
TABLE_HEADER = ("| Id | Estrategia | Tamaño | Caso | N real (pedida) | Mediana (ms) | Q1-Q3 (ms) | IQR (ms) | "
                "Mín-Máx (ms) | Pico (KiB) | Servidor (ms) | Nodo del plan | Notas |")
TABLE_RULE = "|" + "---|" * 13


def build_results_json(params: dict, run_at: str, measurements: list[Measurement]) -> dict:
    """Estructura de `resultados.json` (data-model §2.1), con la etiqueta SINTETICO y la semilla."""
    return {"etiqueta": "SINTETICO", "seed": RNG_SEED, "run_at": run_at, "params": params,
            "measurements": [m.as_dict() for m in measurements]}


def _ms(value: float | None) -> str:
    """Milisegundos con precisión útil (más decimales si el valor es menor que 1 ms)."""
    if value is None:
        return NOT_APPLICABLE
    return f"{value:.6f}" if value < 1 else f"{value:.3f}"


def _row(m: Measurement) -> str:
    """Fila de tabla de una medición; los datos ausentes figuran como «no aplica»."""
    peak = NOT_APPLICABLE if m.peak_kib is None else f"{m.peak_kib:.1f}"
    node = ", ".join(m.nodes[:2]) if m.nodes else NOT_APPLICABLE
    return (f"| {m.id} | {m.strategy} | {m.size} | {m.case} | {m.n_real} ({m.n_requested}) | {_ms(m.median_ms)} | "
            f"{_ms(m.q1_ms)}-{_ms(m.q3_ms)} | {_ms(m.iqr_ms)} | {_ms(m.min_ms)}-{_ms(m.max_ms)} | {peak} | "
            f"{_ms(m.server_ms)} | {node} | {m.notes or NOT_APPLICABLE} |")


def render_tablas_md(measurements: list[Measurement], params: dict) -> str:
    """Genera `tablas.md`: una tabla por operación con unidades, N real y etiqueta SINTÉTICO."""
    lines = [f"# Tablas de mediciones ({SYNTHETIC_LABEL})", "",
             f"Todas las cifras provienen de datos {SYNTHETIC_LABEL} (`bench`, semilla {RNG_SEED}) salvo lo que "
             "se indique como REAL. Tiempos en milisegundos (base decimal, `time.perf_counter`), memoria en KiB "
             "(base 1024, `tracemalloc`), calentamiento descartado. Las consultas se miden desde el cliente "
             "(ida y vuelta incluidas) y el tiempo del servidor sale del plan `EXPLAIN ANALYZE`.", "",
             f"Parámetros: tamaños {params['sizes']}, repeticiones máximas {params['repeats']}, presupuesto "
             f"{params['budget_seconds']} s por serie. N real puede ser menor que la pedida por el presupuesto.", ""]
    for operation, title in OPERATION_TITLES.items():
        group = [m for m in measurements if m.operation == operation]
        if not group:
            continue
        lines += [f"## {title} ({SYNTHETIC_LABEL})", "", TABLE_HEADER, TABLE_RULE]
        lines += [_row(m) for m in sorted(group, key=lambda m: (m.size, m.strategy, m.case))]
        lines.append("")
    return "\n".join(lines)


def render_indices_md(reference: RealReference | None, verdicts: list[Verdict],
                      bench_sizes: list[dict]) -> str:
    """Genera `indices.md`: referencia REAL, veredictos por índice (SINTÉTICO) y tamaños en `bench`."""
    lines = ["# Índices de `live.current_event` (E6)", "",
             "Los veredictos son una PROPUESTA al alumno: no se edita el DDL ni el contrato. Criterio de `verdicts.py`: "
             "«justificado» si el plan usa el índice y baja la mediana sin solape de rangos intercuartílicos.", ""]
    if reference is not None:
        lines += [render_real_reference(reference)]
    lines += [f"## Veredicto por índice ({SYNTHETIC_LABEL})", "", "| Índice | Veredicto global |", "|---|---|"]
    names = sorted({v.index for v in verdicts})
    lines += [f"| {name} | {overall_verdict([v for v in verdicts if v.index == name])} |" for name in names]
    lines += ["", f"## Detalle por consulta y caso ({SYNTHETIC_LABEL})", "",
              "| Índice | Consulta | Caso | Tamaño | Veredicto | Ids citados | Selectividad | Motivo |",
              "|---|---|---|---|---|---|---|---|"]
    for v in verdicts:
        size = v.measurement_ids[0].split(".")[2]
        selectivity = NOT_APPLICABLE if v.selectivity is None else f"{v.selectivity:.4f}"
        lines.append(f"| {v.index} | {v.query} | {v.case} | {size} | {v.verdict} | "
                     f"{v.measurement_ids[0]}; {v.measurement_ids[1]} | {selectivity} | {v.reason} |")
    lines += ["", f"## Tamaño de los índices en `bench` ({SYNTHETIC_LABEL})", "",
              "| Filas | Índice (en `bench`) | Bytes |", "|---|---|---|"]
    for sized in bench_sizes:
        lines += [f"| {sized['rows']} | {name} | {size} |" for name, size in sized["indexes"].items()]
    return "\n".join(lines) + "\n"


def render_aislamiento_md(before: dict, after: dict, problems: list[str]) -> str:
    """Genera `aislamiento.md`: instantáneas antes y después y las violaciones (vacío = correcto)."""
    keys = [k for k in before if k != "bench_rows_outside"]
    lines = ["# Aislamiento de `bench` (K4, FR-017)", "", "| Comprobación | Antes | Después |", "|---|---|---|"]
    lines += [f"| {key} | {before[key]} | {after[key]} |" for key in keys]
    lines += [f"| filas de bench en {table} | {before['bench_rows_outside'][table]} | {count} |"
              for table, count in after["bench_rows_outside"].items()]
    lines += ["", f"Violaciones: {'ninguna' if not problems else '; '.join(problems)}.", ""]
    return "\n".join(lines)
