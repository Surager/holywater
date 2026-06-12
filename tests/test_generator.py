"""Basic smoke tests runnable with plain Python."""

from __future__ import annotations

from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from holywater.db import initialize_database
from holywater.generator import HolyWaterGenerator


def test_database_initializes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        initialize_database(db_path)
        with closing(sqlite3.connect(db_path)) as conn:
            templates = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
            fragments = conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]
        assert templates >= 6
        assert fragments >= 20


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


def test_daily_is_stable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        generator = HolyWaterGenerator(Path(tmp) / "holywater.sqlite3")
        first = generator.daily(style="revelation", mood="absurd", intensity=5, context="gaming")
        second = generator.daily(style="revelation", mood="absurd", intensity=5, context="gaming")
        assert first == second


if __name__ == "__main__":
    test_database_initializes()
    test_seed_reproducible()
    test_daily_is_stable()
    print("All tests passed.")
