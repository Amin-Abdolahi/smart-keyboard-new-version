# tests/test_detector.py
# تست ماژول detector

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartkeyboard.detector import detect


def test_detect_sghl():
    r = detect("sghl", "en", ["fa", "en"])
    assert r.action in ("auto", "suggest")
    assert r.suggested == "سلام"


def test_detect_hello_keep():
    r = detect("hello", "en", ["fa", "en"])
    assert r.action == "keep"


def test_detect_persian_keep():
    r = detect("سلام", "fa", ["fa", "en"])
    assert r.action == "keep"


def test_detect_whitelist_keep():
    r = detect("AI", "fa", ["fa", "en"])
    assert r.action == "keep"


def test_detect_meaningless_keep():
    r = detect("asdfgh", "en", ["fa", "en"])
    assert r.action == "keep"


def test_detect_longer_text():
    r = detect("sghl phgj ]x,vi", "en", ["fa", "en"])
    assert r.action in ("auto", "suggest")
    assert "سلام" in r.suggested