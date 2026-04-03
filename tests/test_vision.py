import json
from unittest.mock import patch, MagicMock
from voherzn.vision import analyze_photo, analyze_photos, analyze_from_text

MOCK_VISION_RESPONSE = {
    "product_name": "Filztasche altrosa",
    "category": "Tasche",
    "materials": ["Filz", "Baumwolle"],
    "colors": ["altrosa", "creme"],
    "features": ["handgenaeht", "Tiermotiv", "Innentasche"],
}


def _mock_client():
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(MOCK_VISION_RESPONSE))]
    mock.messages.create.return_value = mock_message
    return mock


def test_analyze_photo_returns_required_keys():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        result = analyze_photo("tests/fixtures/test.jpg")
    assert "product_name" in result
    assert "category" in result
    assert "materials" in result
    assert "colors" in result
    assert "features" in result


def test_analyze_photo_parses_json():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        result = analyze_photo("tests/fixtures/test.jpg")
    assert result["product_name"] == "Filztasche altrosa"
    assert "Filz" in result["materials"]


def test_analyze_photos_batch():
    with patch("voherzn.vision._get_client", return_value=_mock_client()), \
         patch("voherzn.vision._encode_image", return_value=("AAAA", "image/jpeg")):
        results = analyze_photos(["img1.jpg", "img2.jpg", "img3.jpg"])
    assert len(results) == 3


def test_analyze_photos_max_10():
    with patch("voherzn.vision._get_client", return_value=_mock_client()), \
         patch("voherzn.vision._encode_image", return_value=("AAAA", "image/jpeg")):
        paths = [f"img{i}.jpg" for i in range(15)]
        results = analyze_photos(paths)
    assert len(results) == 10


def test_analyze_from_text():
    with patch("voherzn.vision._get_client", return_value=_mock_client()):
        result = analyze_from_text("Filztasche altrosa, handgenaeht")
    assert isinstance(result, dict)
    assert "product_name" in result
    assert "category" in result
    assert "materials" in result
    assert "colors" in result
    assert "features" in result


def test_json_extraction_from_codeblock():
    wrapped_response = '```json\n' + json.dumps(MOCK_VISION_RESPONSE) + '\n```'
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=wrapped_response)]
    mock.messages.create.return_value = mock_message
    with patch("voherzn.vision._get_client", return_value=mock), \
         patch("voherzn.vision._encode_image", return_value=("AAAA", "image/jpeg")):
        result = analyze_photo("tests/fixtures/test.jpg")
    assert result["product_name"] == "Filztasche altrosa"
    assert "Filz" in result["materials"]
