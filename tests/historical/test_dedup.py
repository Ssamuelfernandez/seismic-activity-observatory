"""Pruebas de la deduplicación por id y updated (T002, B14, SC-003). Datos sintéticos."""
from historical.dedup import dedup_features


def feature(event_id: str | None, updated: object, tag: str = "") -> dict:
    """Feature sintética mínima; `tag` distingue copias del mismo id."""
    result: dict = {"type": "Feature", "properties": {"updated": updated, "tag": tag}}
    if event_id is not None:
        result["id"] = event_id
    return result


def test_same_id_keeps_greater_updated() -> None:
    result = dedup_features([[feature("synthetic-a", 10, "old")], [feature("synthetic-a", 20, "new")]])
    assert len(result.features) == 1
    assert result.features[0]["properties"]["tag"] == "new"
    assert result.discarded == 1


def test_greater_updated_wins_even_if_first() -> None:
    result = dedup_features([[feature("synthetic-a", 20, "new")], [feature("synthetic-a", 10, "old")]])
    assert [f["properties"]["tag"] for f in result.features] == ["new"]
    assert result.discarded == 1


def test_same_updated_keeps_first() -> None:
    result = dedup_features([[feature("synthetic-a", 10, "first")], [feature("synthetic-a", 10, "second")]])
    assert [f["properties"]["tag"] for f in result.features] == ["first"]
    assert result.discarded == 1


def test_without_id_or_bad_updated_passes_ungrouped() -> None:
    items = [feature(None, 1), feature(None, 1), feature("synthetic-b", "x"), feature("synthetic-b", "x"),
             feature("synthetic-c", True), feature("synthetic-c", True)]
    result = dedup_features([items])
    assert len(result.features) == 6
    assert result.discarded == 0


def test_empty_input() -> None:
    result = dedup_features([])
    assert result.features == []
    assert result.discarded == 0
    assert dedup_features([[], []]).features == []


def test_distinct_ids_equal_features_with_id() -> None:
    lists = [[feature("synthetic-a", 1), feature("synthetic-b", 1)],
             [feature("synthetic-b", 2), feature("synthetic-c", 1)]]
    result = dedup_features(lists)
    ids = [f["id"] for f in result.features if "id" in f]
    assert len(set(ids)) == len(ids) == 3
    assert result.discarded == 1
