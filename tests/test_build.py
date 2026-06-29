"""Tests for single-file static HTML compilation."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from holywater.build import compile_static_html, export_corpus
from holywater.generator import HolyWaterGenerator, stable_seed


def test_export_corpus_contains_templates_and_fragments() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        corpus = export_corpus(db_path)
        assert corpus["templates"]
        assert corpus["fragments"]
        assert set(corpus["allowedStyles"]) == {
            "genesis",
            "psalm",
            "proverb",
            "revelation",
            "gospel",
            "commandment",
        }


def test_compile_writes_single_self_contained_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        out = Path(tmp) / "holywater.html"
        compile_static_html(out, db_path, build_date=date(2026, 6, 24))

        html_text = out.read_text(encoding="utf-8")
        assert out.is_file()
        assert "window.__HOLYWATER_CORPUS__" in html_text
        assert "<style>" in html_text
        assert "btn-copy" in html_text
        assert "class Random" in html_text
        assert 'href="assets/' not in html_text
        assert 'src="assets/' not in html_text


def test_embedded_corpus_matches_export() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        out = Path(tmp) / "holywater.html"
        corpus = export_corpus(db_path)
        compile_static_html(out, db_path)

        html_text = out.read_text(encoding="utf-8")
        match = re.search(r"window\.__HOLYWATER_CORPUS__ = (\{.*?\});", html_text, re.S)
        assert match is not None
        embedded = json.loads(match.group(1))
        assert embedded["templates"] == corpus["templates"]
        assert embedded["fragments"] == corpus["fragments"]


def test_daily_seed_matches_python() -> None:
    day = date(2026, 6, 24)
    style = "random"
    mood = "random"
    intensity = None
    context = "random"
    expected_seed = stable_seed(f"{day.isoformat()}:{style}:{mood}:{intensity}:{context}")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        generator = HolyWaterGenerator(db_path)
        python_daily = generator.daily(
            style=style,
            mood=mood,
            intensity=intensity,
            context=context,
            on_date=day,
        )
        assert python_daily.seed == expected_seed


NODE_SNIPPET = """
const fs = require("fs");
const html = fs.readFileSync(process.argv[1], "utf8");
const runtimePath = process.argv[2];
const day = process.argv[3];
globalThis.window = globalThis;
globalThis.__HOLYWATER_CORPUS__ = JSON.parse(
  html.match(/window.__HOLYWATER_CORPUS__ = (\\{.*?\\});/s)[1]
);
require(runtimePath);
const text = globalThis.HolyWater.daily({
  date: day,
  style: "random",
  mood: "random",
  intensity: null,
  context: "random",
});
process.stdout.write(JSON.stringify(text));
"""


def test_daily_output_matches_python_when_node_available() -> None:
    if shutil.which("node") is None:
        return

    day = date(2026, 6, 24)
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "holywater.sqlite3"
        out = Path(tmp) / "holywater.html"
        runtime = Path(__file__).resolve().parents[1] / "src" / "holywater" / "static" / "runtime.js"

        compile_static_html(out, db_path, build_date=day)
        python_daily = HolyWaterGenerator(db_path).daily(on_date=day)

        completed = subprocess.run(
            ["node", "-e", NODE_SNIPPET, str(out), str(runtime), day.isoformat()],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        js_daily = json.loads(completed.stdout)

    assert js_daily["content"] == python_daily.content
    assert js_daily["reference"] == python_daily.reference
    assert js_daily["seed"] == python_daily.seed
