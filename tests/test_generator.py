"""Basic smoke tests runnable with plain Python."""

from __future__ import annotations

from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from holywater.db import CONTEXT_FRAGMENTS, DEPRECATED_TEMPLATES, FRAGMENTS, TEMPLATES, initialize_database
from holywater.generator import ALLOWED_MOODS, ALLOWED_STYLES, HolyWaterGenerator


def test_database_initializes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        initialize_database(db_path)
        with closing(sqlite3.connect(db_path)) as conn:
            templates = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
            fragments = conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]
        assert templates == len(TEMPLATES)
        assert fragments == _expected_fragment_count()


def test_database_seed_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        initialize_database(db_path)
        initialize_database(db_path)
        with closing(sqlite3.connect(db_path)) as conn:
            templates = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
            fragments = conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]
        assert templates == len(TEMPLATES)
        assert fragments == _expected_fragment_count()


def test_deprecated_templates_are_disabled() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        initialize_database(db_path)
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "INSERT INTO templates (style, mood, template, weight, enabled) VALUES (?, ?, ?, ?, ?)",
                ("psalm", "absurd", DEPRECATED_TEMPLATES[0], 1.0, 1),
            )
            conn.commit()
        initialize_database(db_path)
        with closing(sqlite3.connect(db_path)) as conn:
            enabled = conn.execute(
                "SELECT enabled FROM templates WHERE template = ?",
                (DEPRECATED_TEMPLATES[0],),
            ).fetchone()[0]
        assert enabled == 0


def test_seed_reproducible() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        first = generator.generate(
            style="genesis",
            mood="serious",
            intensity=3,
            context="coding",
            seed=123,
            save_history=False,
            avoid_recent=False,
        )
        second = generator.generate(
            style="genesis",
            mood="serious",
            intensity=3,
            context="coding",
            seed=123,
            save_history=False,
            avoid_recent=False,
        )
        assert first == second


def test_numeric_string_seed_is_preserved() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        text = generator.generate(seed="42", save_history=False, avoid_recent=False)
        assert text.seed == 42


def test_default_generation_is_random_but_seeded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        first = generator.generate(seed=99, save_history=False, avoid_recent=False)
        second = generator.generate(seed=99, save_history=False, avoid_recent=False)
        assert first == second
        assert first.style in ALLOWED_STYLES
        assert first.mood in ALLOWED_MOODS


def test_random_style_can_pick_non_genesis() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        styles = {
            generator.generate(seed=seed, save_history=False, avoid_recent=False).style
            for seed in range(20)
        }
        assert styles - {"genesis"}


def test_daily_is_stable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        first = generator.daily(style="revelation", mood="absurd", intensity=5, context="gaming")
        second = generator.daily(style="revelation", mood="absurd", intensity=5, context="gaming")
        assert first == second


def _expected_fragment_count() -> int:
    all_fragments = list(FRAGMENTS)
    for items in CONTEXT_FRAGMENTS.values():
        all_fragments.extend(items)
    return len({(category, value, style, mood) for category, value, style, mood, _ in all_fragments})


if __name__ == "__main__":
    test_database_initializes()
    test_database_seed_is_idempotent()
    test_deprecated_templates_are_disabled()
    test_seed_reproducible()
    test_numeric_string_seed_is_preserved()
    test_default_generation_is_random_but_seeded()
    test_random_style_can_pick_non_genesis()
    test_daily_is_stable()
    print("All tests passed.")
