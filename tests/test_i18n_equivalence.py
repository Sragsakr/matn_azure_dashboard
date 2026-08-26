"""
Phase 1 extraction verification for core/i18n.py.

Proves COLUMN_AR in core/i18n.py is byte-for-byte identical to the
COLUMN_AR dict that lived inline in dashboard_app.py before the Phase 1
split, and that tr()/column_label()/localized_frame() behave the same as
the original global-`is_ar`-based versions.

The original dict is extracted directly from git history
(`git show <pre-refactor-commit>:dashboard_app.py`) via a regex + exec, so
this test cannot silently drift from the real historical source of truth —
it never hand-retypes the 60+ Arabic translation entries.
"""

import re
import subprocess
import os

import pandas as pd
import pytest

from core.i18n import COLUMN_AR, tr, column_label, localized_frame

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The commit immediately before this Phase 1 extraction began.
PRE_REFACTOR_REVISION = "6941bbc"


def _original_column_ar():
    result = subprocess.run(
        ["git", "show", f"{PRE_REFACTOR_REVISION}:dashboard_app.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    source = result.stdout
    match = re.search(r"COLUMN_AR = \{.*?\n\}", source, re.S)
    assert match, "Could not locate COLUMN_AR in the pre-refactor dashboard_app.py"
    namespace = {}
    exec(match.group(0), namespace)
    return namespace["COLUMN_AR"]


def test_column_ar_byte_for_byte_identical_to_pre_refactor_source():
    original = _original_column_ar()
    assert COLUMN_AR == original
    assert len(COLUMN_AR) == len(original)
    # Guard against accidental normalization/whitespace drift on Arabic text.
    for key, value in original.items():
        assert COLUMN_AR[key] == value
        assert type(COLUMN_AR[key]) is str


def test_tr_returns_arabic_when_is_ar_true():
    assert tr("Hello", "مرحبا", True) == "مرحبا"


def test_tr_returns_english_when_is_ar_false():
    assert tr("Hello", "مرحبا", False) == "Hello"


def test_column_label_maps_known_column_when_arabic():
    assert column_label("Total", True) == COLUMN_AR["Total"]


def test_column_label_passthrough_when_english():
    assert column_label("Total", False) == "Total"


def test_column_label_passthrough_unknown_key_even_when_arabic():
    assert column_label("Not A Real Column", True) == "Not A Real Column"


def test_localized_frame_noop_when_english():
    frame = pd.DataFrame({"Total": [1, 2], "Done": [1, 0]})
    result = localized_frame(frame, False)
    assert list(result.columns) == ["Total", "Done"]


def test_localized_frame_renames_columns_when_arabic():
    frame = pd.DataFrame({"Total": [1, 2], "Done": [1, 0]})
    result = localized_frame(frame, True)
    assert list(result.columns) == [COLUMN_AR["Total"], COLUMN_AR["Done"]]
