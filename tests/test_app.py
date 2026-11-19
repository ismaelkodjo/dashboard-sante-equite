from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_loads():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert len(at.tabs) == 4


def test_every_theme_renders():
    at = AppTest.from_file(APP, default_timeout=120).run()
    for theme in at.sidebar.selectbox[0].options:
        at.sidebar.selectbox[0].set_value(theme).run()
        assert not at.exception, theme
