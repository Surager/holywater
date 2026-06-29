"""Compile Holy Water into one self-contained static HTML file."""

from __future__ import annotations

import html
import json
from contextlib import closing
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any

from .db import connect, initialize_database, rows_to_dicts
from .generator import (
    ALLOWED_MOODS,
    ALLOWED_STYLES,
    CONTEXT_KEYWORDS,
    DEFAULT_CONTEXT_CHOICES,
    DEFAULT_INTENSITY_CHOICES,
    DEFAULT_MOOD_CHOICES,
    MODERN_CONTEXTS,
    MODERN_CONTEXT_KEYWORDS,
    REFERENCE_BOOKS,
)

CSS = """\
:root {
  color-scheme: light;
  --ink: #2c2416;
  --muted: #6b5d4a;
  --paper: #f4ead5;
  --paper-deep: #e8d9bc;
  --accent: #3d6b8c;
  --accent-soft: #d4e4ef;
  --border: #c9b896;
  --shadow: rgba(44, 36, 22, 0.12);
  --serif: "Noto Serif SC", "Source Han Serif SC", "Songti SC", Georgia, "Times New Roman", serif;
  --sans: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }

html { font-size: 18px; }

body {
  margin: 0;
  min-height: 100vh;
  font-family: var(--serif);
  color: var(--ink);
  background:
    radial-gradient(circle at 20% 10%, rgba(255, 255, 255, 0.55), transparent 45%),
    radial-gradient(circle at 80% 0%, rgba(212, 228, 239, 0.35), transparent 40%),
    linear-gradient(180deg, var(--paper) 0%, var(--paper-deep) 100%);
}

.page {
  max-width: 42rem;
  margin: 0 auto;
  padding: 2.5rem 1.25rem 4rem;
}

.banner { text-align: center; margin-bottom: 2rem; }
.banner h1 { margin: 0 0 0.35rem; font-size: clamp(1.8rem, 4vw, 2.4rem); letter-spacing: 0.08em; }
.banner p { margin: 0; font-family: var(--sans); font-size: 0.95rem; color: var(--muted); }

.card {
  background: rgba(255, 252, 245, 0.82);
  border: 1px solid var(--border);
  border-radius: 1rem;
  box-shadow: 0 12px 32px var(--shadow);
  padding: 2rem 1.5rem;
}

.verse {
  margin: 0;
  font-size: clamp(1.15rem, 2.8vw, 1.35rem);
  line-height: 1.9;
  text-align: justify;
  text-indent: 2em;
}

.reference {
  display: block;
  margin-top: 1.5rem;
  text-align: right;
  font-size: 0.95rem;
  color: var(--muted);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.25rem;
  font-family: var(--sans);
  font-size: 0.78rem;
}

.tag {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
}

.controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 0.75rem;
  margin-top: 1.5rem;
  font-family: var(--sans);
  font-size: 0.85rem;
}

.controls label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  color: var(--muted);
}

.controls select {
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.45rem 0.55rem;
  font: inherit;
  color: var(--ink);
  background: #fff;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 1.5rem;
}

button {
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #fff;
  color: var(--ink);
  font-family: var(--sans);
  font-size: 0.9rem;
  padding: 0.55rem 1.1rem;
  cursor: pointer;
}

button:hover { background: var(--accent-soft); border-color: var(--accent); }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
button.primary:hover { filter: brightness(1.05); }

.hint, .status {
  margin-top: 1rem;
  text-align: center;
  font-family: var(--sans);
  font-size: 0.82rem;
  color: var(--muted);
}

.footer {
  margin-top: 2rem;
  text-align: center;
  font-family: var(--sans);
  font-size: 0.78rem;
  color: var(--muted);
}
"""

STYLE_OPTIONS = [
    ("random", "随机"),
    ("genesis", "genesis"),
    ("psalm", "psalm"),
    ("proverb", "proverb"),
    ("revelation", "revelation"),
    ("gospel", "gospel"),
    ("commandment", "commandment"),
]

MOOD_OPTIONS = [("random", "随机"), ("serious", "serious"), ("absurd", "absurd")]

INTENSITY_OPTIONS = [("", "随机"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")]

CONTEXT_OPTIONS = [
    ("random", "随机"),
    ("home", "home"),
    ("walk", "walk"),
    ("rest", "rest"),
    ("reading", "reading"),
    ("meal", "meal"),
    ("garden", "garden"),
    ("coding", "coding"),
    ("thesis", "thesis"),
    ("gaming", "gaming"),
    ("none", "none"),
]


def export_corpus(db_path: str | Path | None = None) -> dict[str, Any]:
    """Export enabled templates, fragments, and generator constants as JSON-ready data."""

    path = initialize_database(db_path)
    with closing(connect(path)) as conn:
        templates = rows_to_dicts(
            conn.execute(
                """
                SELECT id, style, mood, template, weight
                FROM templates
                WHERE enabled = 1
                ORDER BY id
                """
            )
        )
        fragments = rows_to_dicts(
            conn.execute(
                """
                SELECT id, category, value, style, mood, weight
                FROM fragments
                ORDER BY id
                """
            )
        )

    return {
        "templates": templates,
        "fragments": fragments,
        "allowedStyles": sorted(ALLOWED_STYLES),
        "allowedMoods": sorted(ALLOWED_MOODS),
        "referenceBooks": {
            style: [list(entry) for entry in books]
            for style, books in REFERENCE_BOOKS.items()
        },
        "contextKeywords": CONTEXT_KEYWORDS,
        "modernContexts": sorted(MODERN_CONTEXTS),
        "modernContextKeywords": list(MODERN_CONTEXT_KEYWORDS),
        "defaultContextChoices": DEFAULT_CONTEXT_CHOICES,
        "defaultMoodChoices": DEFAULT_MOOD_CHOICES,
        "defaultIntensityChoices": DEFAULT_INTENSITY_CHOICES,
    }


def compile_static_html(
    output: str | Path,
    db_path: str | Path | None = None,
    *,
    build_date: date | None = None,
) -> Path:
    """Write one self-contained HTML file with embedded corpus and runtime."""

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    corpus = export_corpus(db_path)
    runtime_js = (files("holywater.static") / "runtime.js").read_text(encoding="utf-8")
    corpus_json = json.dumps(corpus, ensure_ascii=False, separators=(",", ":"))
    corpus_json = corpus_json.replace("</", "<\\/")

    day = build_date or date.today()
    page = _render_page(day=day, css=CSS, corpus_json=corpus_json, runtime_js=runtime_js)
    out.write_text(page, encoding="utf-8")
    return out


def _render_page(*, day: date, css: str, corpus_json: str, runtime_js: str) -> str:
    controls = _render_controls()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Holy Water · 喝水提醒</title>
  <meta name="description" content="圣经风格的喝水提醒文案生成器。">
  <style>
{css}
  </style>
</head>
<body>
  <main class="page">
    <header class="banner">
      <h1>Holy Water</h1>
      <p>圣经风格的喝水提醒 · 编译于 {html.escape(day.isoformat())}</p>
    </header>

    <section class="card">
      <p id="verse-content" class="verse"></p>
      <cite id="verse-reference" class="reference"></cite>
      <div id="verse-meta" class="meta"></div>

      <div class="controls" aria-label="生成选项">
{controls}
      </div>

      <div class="actions">
        <button id="btn-copy" type="button" class="primary">复制到剪贴板</button>
        <button id="btn-daily" type="button">刷新今日经文</button>
        <button id="btn-random" type="button">随机一句</button>
      </div>

      <p id="copy-status" class="status" aria-live="polite"></p>
      <p class="hint">默认显示今日固定文案；改选项后会按同一日期重新计算。</p>
    </section>

    <footer class="footer">
      <p>单文件静态页 · 语料与生成逻辑已全部编译进本页</p>
    </footer>
  </main>
  <script>window.__HOLYWATER_CORPUS__ = {corpus_json};</script>
  <script>
{runtime_js}
  </script>
</body>
</html>
"""


def _render_controls() -> str:
    blocks = [
        _render_select("opt-style", "风格", STYLE_OPTIONS),
        _render_select("opt-mood", "语气", MOOD_OPTIONS),
        _render_select("opt-intensity", "强度", INTENSITY_OPTIONS),
        _render_select("opt-context", "场景", CONTEXT_OPTIONS),
    ]
    return "\n".join(blocks)


def _render_select(element_id: str, label: str, options: list[tuple[str, str]]) -> str:
    option_html = "\n".join(
        f'          <option value="{html.escape(value)}">{html.escape(text)}</option>'
        for value, text in options
    )
    return f"""        <label>
          {html.escape(label)}
          <select id="{html.escape(element_id)}">
{option_html}
          </select>
        </label>"""
