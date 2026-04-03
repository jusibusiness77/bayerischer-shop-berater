from __future__ import annotations

from datetime import date, timedelta
from typing import Optional


SEASON_DATA = {
    "Fruehling": {
        "keywords": ["Fruehlingsdeko", "Fruehling", "Naturerwachen", "Blumen"],
        "hashtags": ["#fruehlingsdeko", "#fruehling", "#springvibes", "#blumenliebe"],
        "mood": "frisch, farbenfroh, Aufbruchstimmung",
    },
    "Sommer": {
        "keywords": ["Sommerdeko", "Sommer", "Sonnenschein", "Gartenzeit"],
        "hashtags": ["#sommerdeko", "#sommer", "#summervibes", "#gartenliebe"],
        "mood": "sonnig, leicht, lebensfroh",
    },
    "Herbst": {
        "keywords": ["Herbstdeko", "Herbst", "Kuschelig", "Ernte"],
        "hashtags": ["#herbstdeko", "#herbst", "#autumnvibes", "#gemütlich"],
        "mood": "warm, gemütlich, erdverbunden",
    },
    "Winter": {
        "keywords": ["Winterdeko", "Winter", "Gemütlichkeit", "Kerzenschein"],
        "hashtags": ["#winterdeko", "#winter", "#wintervibes", "#gemütlichkeit"],
        "mood": "besinnlich, warm, geborgen",
    },
}

EVENT_DATA = {
    "Ostern": {
        "keywords": ["Ostern", "Osterdeko", "Ostergeschenk", "Frühlingsfest"],
        "hashtags": ["#ostern", "#osterdeko", "#ostergeschenk", "#happyeaster"],
    },
    "Muttertag": {
        "keywords": ["Muttertag", "Mama", "Geschenk für Mama", "Muttertagsgeschenk"],
        "hashtags": ["#muttertag", "#mama", "#muttertagsgeschenk", "#besteMama"],
    },
    "Halloween": {
        "keywords": ["Halloween", "Halloweendeko", "Gruselig", "Kürbis"],
        "hashtags": ["#halloween", "#halloweendeko", "#spooky", "#kürbis"],
    },
    "Weihnachten": {
        "keywords": ["Weihnachten", "Advent", "Weihnachtsdeko", "Christkind"],
        "hashtags": ["#weihnachten", "#advent", "#weihnachtsdeko", "#christkind"],
    },
    "Valentinstag": {
        "keywords": ["Valentinstag", "Liebe", "Valentinsgeschenk", "Herz"],
        "hashtags": ["#valentinstag", "#liebe", "#valentinsgeschenk", "#herzchen"],
    },
}


def _easter(year: int) -> date:
    """Gauss algorithm for Easter Sunday."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _muttertag(year: int) -> date:
    """2nd Sunday in May."""
    d = date(year, 5, 1)
    days_until_sunday = (6 - d.weekday()) % 7
    first_sunday = d + timedelta(days=days_until_sunday)
    return first_sunday + timedelta(days=7)


def _get_season(d: date) -> str:
    month = d.month
    if month in (3, 4, 5):
        return "Fruehling"
    if month in (6, 7, 8):
        return "Sommer"
    if month in (9, 10, 11):
        return "Herbst"
    return "Winter"


def _active_events(d: date) -> list[str]:
    events = []

    easter = _easter(d.year)
    if easter - timedelta(days=21) <= d <= easter:
        events.append("Ostern")

    mt = _muttertag(d.year)
    if mt - timedelta(days=21) <= d <= mt:
        events.append("Muttertag")

    if d.month == 10:
        events.append("Halloween")

    # Weihnachten/Advent: Nov 20 - Jan 6
    if (d.month == 11 and d.day >= 20) or d.month == 12:
        events.append("Weihnachten")
    elif d.month == 1 and d.day <= 6:
        events.append("Weihnachten")

    # Valentinstag: 14 days before until Feb 14
    valentinstag = date(d.year, 2, 14)
    if valentinstag - timedelta(days=14) <= d <= valentinstag:
        events.append("Valentinstag")

    return events


def get_season_context(d: Optional[date] = None) -> dict:
    if d is None:
        d = date.today()

    season = _get_season(d)
    events = _active_events(d)

    keywords = list(SEASON_DATA[season]["keywords"])
    hashtags = list(SEASON_DATA[season]["hashtags"])

    for event in events:
        keywords.extend(EVENT_DATA[event]["keywords"])
        hashtags.extend(EVENT_DATA[event]["hashtags"])

    return {
        "season": season,
        "events": events,
        "keywords": keywords,
        "hashtags": hashtags,
        "mood": SEASON_DATA[season]["mood"],
    }
