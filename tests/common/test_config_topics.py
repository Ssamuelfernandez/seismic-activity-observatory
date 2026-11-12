"""Pruebas de `load_consumer_topics`: topics del consumidor desde el entorno (J3, FR-008)."""
import pytest

from common.config import ConfigError, load_consumer_topics

VARIABLE = "KAFKA_CONSUMER_TOPICS"


def test_default_is_both_contract_topics(monkeypatch):
    monkeypatch.delenv(VARIABLE, raising=False)
    assert load_consumer_topics() == ("earthquakes.live", "earthquakes.replay")


def test_single_topic_is_accepted(monkeypatch):
    monkeypatch.setenv(VARIABLE, "earthquakes.live")
    assert load_consumer_topics() == ("earthquakes.live",)


def test_spaces_and_duplicates_are_ignored(monkeypatch):
    monkeypatch.setenv(VARIABLE, " earthquakes.replay , earthquakes.live,earthquakes.replay")
    assert load_consumer_topics() == ("earthquakes.replay", "earthquakes.live")


def test_unknown_topic_names_the_variable_and_the_topic(monkeypatch):
    monkeypatch.setenv(VARIABLE, "earthquakes.live,otro.topic")
    with pytest.raises(ConfigError, match=VARIABLE) as error:
        load_consumer_topics()
    assert "otro.topic" in str(error.value)


@pytest.mark.parametrize("value", ["", " , ,"])
def test_empty_value_is_rejected(monkeypatch, value):
    monkeypatch.setenv(VARIABLE, value)
    with pytest.raises(ConfigError, match=VARIABLE):
        load_consumer_topics()
