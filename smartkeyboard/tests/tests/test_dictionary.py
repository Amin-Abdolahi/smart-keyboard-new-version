# tests/test_dictionary.py
# تست ماژول dictionary

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartkeyboard.dictionary import get_dictionary


def test_persian_word():
    d = get_dictionary()
    assert d.is_persian_word("سلام") is True
    assert d.is_persian_word("خوبی") is True


def test_english_word():
    d = get_dictionary()
    assert d.is_english_word("hello") is True
    assert d.is_english_word("world") is True


def test_not_persian_word():
    d = get_dictionary()
    assert d.is_persian_word("asdfgh") is False


def test_not_english_word():
    d = get_dictionary()
    assert d.is_english_word("sghl") is False


def test_whitelist():
    d = get_dictionary()
    assert d.is_whitelisted("AI") is True
    assert d.is_whitelisted("API") is True


def test_stats():
    d = get_dictionary()
    stats = d.stats()
    assert "builtin_fa" in stats
    assert "builtin_en" in stats
    assert stats["builtin_fa"] > 0