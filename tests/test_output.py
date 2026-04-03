import os
from datetime import date
from voherzn.output import OutputManager


def test_creates_desktop_directory(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    assert os.path.isdir(om.root)
    assert "2026-04-03" in om.root


def test_creates_subdirectories(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    assert os.path.isdir(om.etsy_dir)
    assert os.path.isdir(om.instagram_dir)


def test_save_etsy_listing(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    path = om.save_etsy_listing("Filztasche", "TITEL:\nTest\n\nBESCHREIBUNG:\nTest\n\nTAGS:\na,b,c")
    assert os.path.isfile(path)
    assert "filztasche" in path.lower()


def test_save_etsy_csv(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    rows = [{"titel": "Filztasche", "preis": "29.90"}]
    path = om.save_etsy_csv(rows)
    assert os.path.isfile(path)
    assert "alle-listings.csv" in path


def test_save_instagram_caption(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    path = om.save_instagram_caption("Filztasche", "Tolle Caption #voherzn")
    assert os.path.isfile(path)


def test_save_instagram_image(tmp_path):
    from PIL import Image
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    img = Image.new("RGB", (100, 100), "red")
    path = om.save_instagram_image("Filztasche", img)
    assert os.path.isfile(path)
    assert path.endswith(".png")


def test_save_summary(tmp_path):
    om = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    path = om.save_summary(["Filztasche: Etsy + Instagram erstellt"])
    assert os.path.isfile(path)
    assert "zusammenfassung" in path.lower()


def test_duplicate_date_gets_counter(tmp_path):
    om1 = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    om2 = OutputManager(base_dir=str(tmp_path), d=date(2026, 4, 3))
    assert om1.root != om2.root
    assert "_1" in om2.root or "_2" in om2.root


def test_slugify():
    from voherzn.output import _slugify
    assert _slugify("Filztasche Blau") == "filztasche-blau"
    assert _slugify("Öko & Fair!") == "ko-fair"
