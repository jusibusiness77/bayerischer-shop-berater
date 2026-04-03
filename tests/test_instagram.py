import os
from unittest.mock import patch, MagicMock
from voherzn.instagram import generate_caption, create_post_image

MOCK_PRODUCT = {
    "product_name": "Filztasche altrosa",
    "category": "Tasche",
    "materials": ["Filz"],
    "colors": ["altrosa"],
    "features": ["handgenaeht"],
}

MOCK_SEASON = {
    "season": "Fruehling",
    "events": ["Muttertag"],
    "keywords": ["Muttertagsgeschenk"],
    "hashtags": ["#muttertag", "#fruehlingsdeko"],
    "mood": "frisch, farbenfroh",
}

MOCK_CAPTION = """Vo Herz'n — mit Liebe handgemacht!

Unsere neue Filztasche in zartem Altrosa ist da!

#voherzn #handgemacht #muttertag #bayern #filztasche"""


def _mock_client():
    mock = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=MOCK_CAPTION)]
    mock.messages.create.return_value = mock_message
    return mock


def test_generate_caption_returns_text():
    with patch("voherzn.instagram._get_client", return_value=_mock_client()):
        caption = generate_caption(MOCK_PRODUCT, MOCK_SEASON)
    assert isinstance(caption, str)
    assert len(caption) > 0


def test_generate_caption_has_hashtags():
    with patch("voherzn.instagram._get_client", return_value=_mock_client()):
        caption = generate_caption(MOCK_PRODUCT, MOCK_SEASON)
    assert "#" in caption


def test_create_post_image_returns_pil_image():
    img = create_post_image("Neue Filztasche — vo Herz'n")
    assert img.size == (1080, 1080)


def test_create_post_image_saveable(tmp_path):
    img = create_post_image("Test")
    path = os.path.join(str(tmp_path), "test.png")
    img.save(path, "PNG")
    assert os.path.isfile(path)
