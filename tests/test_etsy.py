from unittest.mock import patch, MagicMock
from voherzn.etsy import generate_listing

MOCK_PRODUCT = {
    "product_name": "Filztasche altrosa",
    "category": "Tasche",
    "materials": ["Filz", "Baumwolle"],
    "colors": ["altrosa", "creme"],
    "features": ["handgenaeht", "Tiermotiv"],
}

MOCK_SEASON = {
    "season": "Fruehling",
    "events": ["Muttertag"],
    "keywords": ["Muttertagsgeschenk"],
    "hashtags": [],
    "mood": "frisch, farbenfroh",
}

MOCK_LISTING_TEXT = """TITEL:
Filztasche altrosa handgemacht | Geschenk Muttertag | Handtasche Bayern

BESCHREIBUNG:
Eine wunderschoene Filztasche in zartem Altrosa, mit viel Liebe handgenaeht.

TAGS:
Filztasche, altrosa, handgemacht, Muttertag, Bayern, Geschenk, Handtasche, Unikat, Deko, handgenaeht, Tasche, Filz, Liebe"""


def _mock_client():
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=MOCK_LISTING_TEXT)]
    mock.messages.create.return_value = mock_message
    return mock


def test_generate_listing_returns_required_sections():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert "title" in result
    assert "description" in result
    assert "tags" in result


def test_generate_listing_has_13_tags():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert len(result["tags"]) == 13


def test_generate_listing_title_max_140():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert len(result["title"]) <= 140


def test_generate_listing_raw_text():
    with patch("voherzn.etsy._get_client", return_value=_mock_client()):
        result = generate_listing(MOCK_PRODUCT, MOCK_SEASON)
    assert "raw" in result
    assert "TITEL:" in result["raw"]
