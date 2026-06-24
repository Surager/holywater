"""Basic smoke tests runnable with plain Python."""

from __future__ import annotations

from pathlib import Path
from contextlib import closing
import os
import re
import sqlite3
import sys
import tempfile

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from holywater.db import CONTEXT_FRAGMENTS, DEPRECATED_TEMPLATES, FRAGMENTS, SCHEMA, TEMPLATES, initialize_database
from holywater.api import app
from holywater.generator import (
    ALLOWED_MOODS,
    ALLOWED_STYLES,
    DEFAULT_CONTEXT_CHOICES,
    DEFAULT_MOOD_CHOICES,
    MODERN_CONTEXT_KEYWORDS,
    MODERN_CONTEXTS,
    REFERENCE_BOOKS,
    HolyWaterGenerator,
    _env_int,
)


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


def test_force_seed_refresh_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        initialize_database(db_path)
        initialize_database(db_path, force_seed=True)
        initialize_database(db_path, force_seed=True)
        with closing(sqlite3.connect(db_path)) as conn:
            templates = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
            fragments = conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]
        assert templates == len(TEMPLATES)
        assert fragments == _expected_fragment_count()


def test_initialize_dedupes_legacy_seed_duplicates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        with closing(sqlite3.connect(db_path)) as conn:
            conn.executescript(SCHEMA)
            conn.executemany(
                "INSERT INTO templates (style, mood, template, weight, enabled) VALUES (?, ?, ?, ?, ?)",
                [TEMPLATES[0], TEMPLATES[0]],
            )
            conn.executemany(
                "INSERT INTO fragments (category, value, style, mood, weight) VALUES (?, ?, ?, ?, ?)",
                [FRAGMENTS[0], FRAGMENTS[0]],
            )
            conn.commit()
        initialize_database(db_path)
        with closing(sqlite3.connect(db_path)) as conn:
            template_count = conn.execute(
                "SELECT COUNT(*) FROM templates WHERE style = ? AND mood = ? AND template = ?",
                TEMPLATES[0][:3],
            ).fetchone()[0]
            fragment_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM fragments
                WHERE category = ?
                  AND value = ?
                  AND (style IS ? OR style = ?)
                  AND (mood IS ? OR mood = ?)
                """,
                (FRAGMENTS[0][0], FRAGMENTS[0][1], FRAGMENTS[0][2], FRAGMENTS[0][2], FRAGMENTS[0][3], FRAGMENTS[0][3]),
            ).fetchone()[0]
        assert template_count == 1
        assert fragment_count == 1


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


def test_default_context_choices_favor_neutral_life() -> None:
    modern_count = sum(1 for context in DEFAULT_CONTEXT_CHOICES if context in MODERN_CONTEXTS)
    neutral_count = len(DEFAULT_CONTEXT_CHOICES) - modern_count
    assert neutral_count > modern_count


def test_default_mood_choices_favor_serious() -> None:
    assert DEFAULT_MOOD_CHOICES.count("serious") > DEFAULT_MOOD_CHOICES.count("absurd")


def test_random_style_can_pick_non_genesis() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        styles = {
            generator.generate(seed=seed, save_history=False, avoid_recent=False).style
            for seed in range(20)
        }
        assert styles - {"genesis"}


def test_reference_books_are_varied_by_style() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        for style in ALLOWED_STYLES:
            references = {
                generator.generate(
                    style=style,
                    seed=seed,
                    save_history=False,
                    avoid_recent=False,
                ).reference
                for seed in range(40)
            }
            book_names = {_reference_book(reference) for reference in references}
            allowed_books = {book for book, _, _ in REFERENCE_BOOKS[style]}
            assert book_names <= allowed_books
            assert len(book_names) >= 2


def test_history_cleanup_respects_max_rows() -> None:
    old_value = os.environ.get("HOLYWATER_HISTORY_MAX_ROWS")
    os.environ["HOLYWATER_HISTORY_MAX_ROWS"] = "3"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "holywater.sqlite3"
            generator = HolyWaterGenerator(db_path)
            for seed in range(8):
                generator.generate(seed=seed)
            with closing(sqlite3.connect(db_path)) as conn:
                count = conn.execute("SELECT COUNT(*) FROM generation_history").fetchone()[0]
            assert count == 3
    finally:
        _restore_env("HOLYWATER_HISTORY_MAX_ROWS", old_value)


def test_history_cleanup_respects_retention_days() -> None:
    old_days = os.environ.get("HOLYWATER_HISTORY_RETENTION_DAYS")
    old_rows = os.environ.get("HOLYWATER_HISTORY_MAX_ROWS")
    os.environ["HOLYWATER_HISTORY_RETENTION_DAYS"] = "1"
    os.environ["HOLYWATER_HISTORY_MAX_ROWS"] = "0"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "holywater.sqlite3"
            generator = HolyWaterGenerator(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO generation_history (text, style, mood, created_at)
                    VALUES (?, ?, ?, datetime('now', '-3 days'))
                    """,
                    ("old", "genesis", "serious"),
                )
                conn.commit()
            generator.generate(seed=1)
            with closing(sqlite3.connect(db_path)) as conn:
                texts = [row[0] for row in conn.execute("SELECT text FROM generation_history").fetchall()]
            assert "old" not in texts
            assert texts
    finally:
        _restore_env("HOLYWATER_HISTORY_RETENTION_DAYS", old_days)
        _restore_env("HOLYWATER_HISTORY_MAX_ROWS", old_rows)


def test_history_env_values_are_clamped() -> None:
    old_days = os.environ.get("HOLYWATER_HISTORY_RETENTION_DAYS")
    old_rows = os.environ.get("HOLYWATER_HISTORY_MAX_ROWS")
    os.environ["HOLYWATER_HISTORY_RETENTION_DAYS"] = "-1"
    os.environ["HOLYWATER_HISTORY_MAX_ROWS"] = "2000000"
    try:
        assert _env_int("HOLYWATER_HISTORY_RETENTION_DAYS", 7) == 0
        assert _env_int("HOLYWATER_HISTORY_MAX_ROWS", 5000) == 1_000_000
    finally:
        _restore_env("HOLYWATER_HISTORY_RETENTION_DAYS", old_days)
        _restore_env("HOLYWATER_HISTORY_MAX_ROWS", old_rows)


def test_api_rejects_invalid_parameters() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        old_db = os.environ.get("HOLYWATER_DB")
        os.environ["HOLYWATER_DB"] = str(Path(tmp) / "holywater.sqlite3")
        try:
            with TestClient(app) as client:
                response = client.get("/generate", params={"style": "invalid"})
                assert response.status_code == 422
                response = client.get("/generate", params={"intensity": 99})
                assert response.status_code == 422
        finally:
            _restore_env("HOLYWATER_DB", old_db)


def test_api_generate_uses_lifespan_generator() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        old_db = os.environ.get("HOLYWATER_DB")
        os.environ["HOLYWATER_DB"] = str(Path(tmp) / "holywater.sqlite3")
        try:
            with TestClient(app) as client:
                response = client.get("/generate", params={"seed": "123"})
                assert response.status_code == 200
                payload = response.json()
                assert payload["seed"] == 123
                assert payload["content"]
        finally:
            _restore_env("HOLYWATER_DB", old_db)


def test_neutral_context_filters_modern_fragments() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        for seed in range(30):
            text = generator.generate(
                context="none",
                seed=seed,
                save_history=False,
                avoid_recent=False,
            )
            assert not any(keyword in text.content for keyword in MODERN_CONTEXT_KEYWORDS)


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


def _reference_book(reference: str) -> str:
    match = re.fullmatch(r"《(.+)》\d+:\d+", reference)
    assert match is not None
    return match.group(1)


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    test_database_initializes()
    test_database_seed_is_idempotent()
    test_force_seed_refresh_is_idempotent()
    test_initialize_dedupes_legacy_seed_duplicates()
    test_deprecated_templates_are_disabled()
    test_seed_reproducible()
    test_numeric_string_seed_is_preserved()
    test_default_generation_is_random_but_seeded()
    test_default_context_choices_favor_neutral_life()
    test_default_mood_choices_favor_serious()
    test_random_style_can_pick_non_genesis()
    test_reference_books_are_varied_by_style()
    test_history_cleanup_respects_max_rows()
    test_history_cleanup_respects_retention_days()
    test_history_env_values_are_clamped()
    test_api_rejects_invalid_parameters()
    test_api_generate_uses_lifespan_generator()
    test_neutral_context_filters_modern_fragments()
    test_daily_is_stable()
    print("All tests passed.")
