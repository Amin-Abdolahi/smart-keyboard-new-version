# tests/test_converter.py
# تست ماژول converter

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartkeyboard.converter import convert_text, detect_case, apply_case


def test_en_to_fa_basic():
    assert convert_text("sghl", "en", "fa") == "سلام"


def test_fa_to_en_basic():
    assert convert_text("سلام", "fa", "en") == "sghl"


def test_en_to_fa_longer():
    assert convert_text("sghl phgj ]x,vi", "en", "fa") == "سلام حالت چطوره"


def test_same_lang():
    assert convert_text("hello", "en", "en") == "hello"
    assert convert_text("سلام", "fa", "fa") == "سلام"


def test_empty_string():
    assert convert_text("", "en", "fa") == ""


def test_detect_case_lower():
    assert detect_case("hello") == "lower"


def test_detect_case_upper():
    assert detect_case("HELLO") == "upper"


def test_detect_case_title():
    assert detect_case("Hello") == "title"


def test_detect_case_mixed():
    assert detect_case("HeLLo") == "mixed"


def test_apply_case_lower():
    assert apply_case("HELLO", "lower") == "hello"


def test_apply_case_upper():
    assert apply_case("hello", "upper") == "HELLO"


def test_apply_case_title():
    assert apply_case("hello world", "title") == "Hello World"