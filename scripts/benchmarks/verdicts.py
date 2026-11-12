"""Veredicto puro sobre un índice a partir de las mediciones sin y con él (E6, D8).

Solo es una recomendación para el alumno: no edita DDL ni contratos. Cada veredicto cita los
identificadores de las dos mediciones en que se apoya.
"""
from dataclasses import dataclass

from scripts.benchmarks.records import Measurement
from scripts.benchmarks.stats import N_MIN

JUSTIFIED = "justificado"
NOT_JUSTIFIED = "no justificado con estos datos"
INCONCLUSIVE = "no concluyente"


@dataclass(frozen=True)
class Verdict:
    """Veredicto de un índice para una consulta y un caso, con los ids que lo sustentan."""

    index: str
    query: str
    case: str
    verdict: str
    measurement_ids: tuple[str, str]
    reason: str
    selectivity: float | None = None


def _overlap(a: Measurement, b: Measurement) -> bool:
    """True si los rangos intercuartílicos [q1, q3] de las dos mediciones se solapan."""
    return a.q1_ms <= b.q3_ms and b.q1_ms <= a.q3_ms


def judge(index: str, query: str, without: Measurement, with_index: Measurement,
          selectivity: float | None = None) -> Verdict:
    """Decide el veredicto de un índice para una consulta y un caso.

    Qué hace:
        «No concluyente» si alguna serie tiene menos de 3 repeticiones o los rangos
        intercuartílicos se solapan; «no justificado con estos datos» si el plan no usa el índice
        o con él no es más rápido; «justificado» si lo usa y baja el tiempo sin solape de rangos.
    Recibe:
        index, query: nombre del índice y de la consulta; without, with_index: mediciones sin y con
        él; selectivity: fracción de filas que selecciona el filtro (opcional).
    Devuelve:
        `Verdict` con los ids de las dos mediciones.
    Por qué existe:
        El criterio es el mismo para todos los índices y queda citado (E6, FR-005).
    """
    ids = (without.id, with_index.id)
    make = lambda verdict, reason: Verdict(index, query, with_index.case, verdict, ids, reason, selectivity)
    if min(without.n_real, with_index.n_real) < N_MIN:
        return make(INCONCLUSIVE, f"menos de {N_MIN} repeticiones")
    if not with_index.index_used:
        return make(NOT_JUSTIFIED, "el planificador no usa el índice")
    if _overlap(without, with_index):
        return make(INCONCLUSIVE, "los rangos intercuartílicos se solapan")
    if with_index.median_ms < without.median_ms:
        return make(JUSTIFIED, f"usa el índice y baja la mediana de {without.median_ms:.3f} a "
                               f"{with_index.median_ms:.3f} ms")
    return make(NOT_JUSTIFIED, "usa el índice pero no es más rápido")


def overall_verdict(verdicts: list[Verdict]) -> str:
    """Veredicto global de un índice: justificado si algún caso lo es; si no, no concluyente si lo hay."""
    kinds = {v.verdict for v in verdicts}
    if JUSTIFIED in kinds:
        return JUSTIFIED
    return INCONCLUSIVE if INCONCLUSIVE in kinds else NOT_JUSTIFIED
