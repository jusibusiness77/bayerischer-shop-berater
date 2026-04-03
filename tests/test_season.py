from datetime import date
from voherzn.season import get_season_context


def test_muttertag_3_weeks_before():
    ctx = get_season_context(date(2026, 4, 20))
    assert "Muttertag" in ctx["events"]
    assert any("Muttertag" in kw or "Mama" in kw for kw in ctx["keywords"])


def test_weihnachten_advent():
    ctx = get_season_context(date(2026, 12, 5))
    assert "Weihnachten" in ctx["events"]
    assert ctx["season"] == "Winter"


def test_ostern():
    ctx = get_season_context(date(2026, 3, 20))
    assert "Ostern" in ctx["events"]


def test_sommer_keine_feiertage():
    ctx = get_season_context(date(2026, 7, 15))
    assert ctx["season"] == "Sommer"
    assert len(ctx["events"]) == 0


def test_context_has_required_keys():
    ctx = get_season_context(date(2026, 6, 1))
    assert "season" in ctx
    assert "events" in ctx
    assert "keywords" in ctx
    assert "hashtags" in ctx
    assert "mood" in ctx
