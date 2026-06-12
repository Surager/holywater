"""SQLite storage and seed data for templates, fragments, and history."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DB_PATH = Path.home() / ".holywater" / "holywater.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style TEXT NOT NULL,
    mood TEXT NOT NULL,
    template TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fragments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    value TEXT NOT NULL,
    style TEXT,
    mood TEXT,
    weight REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS generation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    style TEXT NOT NULL,
    mood TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_templates_lookup
    ON templates (style, mood, enabled);

CREATE INDEX IF NOT EXISTS idx_fragments_lookup
    ON fragments (category, style, mood);

CREATE INDEX IF NOT EXISTS idx_generation_history_recent
    ON generation_history (style, mood, created_at);
"""


TEMPLATES: list[tuple[str, str, str, float, int]] = [
    (
        "genesis",
        "serious",
        "{time_phrase}，{subject}见{water_object}，便说：“{divine_command}。”于是{action}，{result}。",
        1.4,
        1,
    ),
    (
        "genesis",
        "absurd",
        "{time_phrase}，{subject}在{context_scene}中看见{water_object}，其上有光，便听见声说：“{divine_command}。”于是{action}，{absurd_result}。",
        1.2,
        1,
    ),
    (
        "psalm",
        "serious",
        "{subject}啊，当在{context_scene}中记念{water_object}；因{result}，你的{body_part}也必安稳。",
        1.2,
        1,
    ),
    (
        "psalm",
        "absurd",
        "{subject}啊，愿你的{body_part}不再像{absurd_image}；你当{action}，并歌唱说：“{divine_command}。”",
        1.1,
        1,
    ),
    (
        "proverb",
        "serious",
        "智慧人见{water_object}便{action}；愚昧人等到{body_part}干涸，才说：“{divine_command}。”",
        1.3,
        1,
    ),
    (
        "proverb",
        "absurd",
        "宁可在{context_scene}中饮一口清水，不可让{absurd_image}在你{body_part}上开会。",
        1.0,
        1,
    ),
    (
        "revelation",
        "serious",
        "{time_phrase}，我又看见{water_object}如明亮的河，从杯中出来；有声音说：“{divine_command}。”{result}。",
        1.0,
        1,
    ),
    (
        "revelation",
        "absurd",
        "{time_phrase}，第{omen_number}杯揭开了，{absurd_image}从{context_scene}升起；那声音如众键盘说：“{divine_command}。”于是{action}，{absurd_result}。",
        1.4,
        1,
    ),
    (
        "gospel",
        "serious",
        "{subject}来到{context_scene}，{mentor}对他说：“{divine_command}。”他便{action}，{result}。",
        1.1,
        1,
    ),
    (
        "gospel",
        "absurd",
        "{mentor}见{subject}在{context_scene}里枯坐，就递给他{water_object}，说：“{divine_command}。”众人便稀奇。",
        1.0,
        1,
    ),
    (
        "commandment",
        "serious",
        "你当{action}，不可藐视{water_object}；因这是给{context_scene}中人的诫命。",
        1.3,
        1,
    ),
    (
        "commandment",
        "absurd",
        "第一条诫命乃是：{divine_command}。第二条也相仿：不可让{absurd_image}替你管理{body_part}。",
        1.2,
        1,
    ),
]


FRAGMENTS: list[tuple[str, str, str | None, str | None, float]] = [
    ("time_phrase", "到了第三时辰", None, "serious", 1.2),
    ("time_phrase", "日头正高的时候", "genesis", "serious", 1.0),
    ("time_phrase", "夜尽天明的时候", "gospel", "serious", 0.9),
    ("time_phrase", "第七个提醒响起的时候", "revelation", "absurd", 1.4),
    ("time_phrase", "当进度条走到旷野中央", None, "absurd", 1.0),
    ("subject", "那口渴的人", None, "serious", 1.3),
    ("subject", "守着屏幕的人", None, None, 1.0),
    ("subject", "久坐的仆人", None, "serious", 1.0),
    ("subject", "被截止日期追赶的人", None, None, 0.9),
    ("subject", "手握鼠标的选民", None, "absurd", 1.0),
    ("water_object", "杯中的清水", None, "serious", 1.4),
    ("water_object", "桌旁的水杯", None, None, 1.2),
    ("water_object", "生命的泉水", "revelation", "serious", 1.1),
    ("water_object", "那盏未被垂青的保温杯", None, "absurd", 1.2),
    ("divine_command", "要喝水", None, "serious", 1.8),
    ("divine_command", "起来，举杯，不要让喉咙荒凉", None, "serious", 1.0),
    ("divine_command", "饮吧，因为缓存不会替你补水", None, "absurd", 1.2),
    ("divine_command", "不可把口渴推迟到世界的末了", "revelation", "absurd", 1.4),
    ("action", "他举杯饮下", None, "serious", 1.5),
    ("action", "他喝了一大口", None, None, 1.2),
    ("action", "他停下手中的工，缓缓饮水", None, "serious", 1.0),
    ("action", "他像打开约柜一样打开瓶盖", None, "absurd", 1.1),
    ("result", "其喉便不再干涸", None, "serious", 1.4),
    ("result", "心里也得了片刻安息", None, "serious", 1.1),
    ("result", "思路如溪水重新流动", None, None, 1.0),
    ("result", "干渴退去，如黑暗离开晨光", "genesis", "serious", 1.0),
    ("absurd_result", "键盘上的尘土也俯伏称善", None, "absurd", 1.0),
    ("absurd_result", "他的喉咙停止发布灾难预言", None, "absurd", 1.2),
    ("absurd_result", "杯子便在桌上得了荣耀", None, "absurd", 1.0),
    ("context_scene", "案头", None, None, 0.8),
    ("context_scene", "代码的葡萄园", None, None, 1.0),
    ("context_scene", "论文的旷野", None, None, 1.0),
    ("context_scene", "排位赛的战场", None, None, 1.0),
    ("context_scene", "会议的会幕", None, None, 0.9),
    ("body_part", "喉咙", None, "serious", 1.3),
    ("body_part", "舌头", None, None, 1.0),
    ("body_part", "脑袋", None, "absurd", 0.8),
    ("mentor", "那智慧的提醒者", "gospel", "serious", 1.0),
    ("mentor", "坐在旁边的人", "gospel", None, 0.8),
    ("mentor", "水杯的见证人", "gospel", "absurd", 1.1),
    ("omen_number", "三", "revelation", None, 1.0),
    ("omen_number", "七", "revelation", None, 1.2),
    ("omen_number", "十二", "revelation", "absurd", 0.9),
    ("absurd_image", "沙漠里的打印机", None, "absurd", 1.0),
    ("absurd_image", "发热的显卡之兽", None, "absurd", 1.1),
    ("absurd_image", "干裂的番茄钟", None, "absurd", 1.0),
]


CONTEXT_FRAGMENTS: dict[str, list[tuple[str, str, str | None, str | None, float]]] = {
    "coding": [
        ("context_scene", "代码的葡萄园", None, None, 2.0),
        ("context_scene", "终端的门口", None, None, 1.4),
        ("subject", "调试到第七层的人", None, None, 1.4),
        ("result", "思路如溪水重新流动", None, None, 1.7),
        ("divine_command", "先喝水，再审判这个异常", None, "absurd", 1.3),
    ],
    "thesis": [
        ("context_scene", "论文的旷野", None, None, 2.0),
        ("subject", "被脚注围困的人", None, None, 1.5),
        ("result", "段落之间便有了气息", None, "serious", 1.4),
        ("divine_command", "喝水，然后继续修订", None, "serious", 1.2),
    ],
    "gaming": [
        ("context_scene", "排位赛的战场", None, None, 2.0),
        ("subject", "守着复活倒计时的人", None, None, 1.5),
        ("result", "手心不再像荒地", None, "serious", 1.2),
        ("divine_command", "趁加载的时候喝水", None, "absurd", 1.6),
        ("absurd_image", "发热的显卡之兽", None, "absurd", 1.8),
    ],
}


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection and return rows as dictionary-like objects."""

    path = Path(db_path or os.getenv("HOLYWATER_DB") or DEFAULT_DB_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        if db_path or os.getenv("HOLYWATER_DB"):
            raise
        path = Path.cwd() / ".holywater" / "holywater.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: str | Path | None = None, *, force_seed: bool = False) -> Path:
    """Create tables and insert bundled examples when the database is empty."""

    path = Path(db_path or os.getenv("HOLYWATER_DB") or DEFAULT_DB_PATH)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        if db_path or os.getenv("HOLYWATER_DB"):
            raise
        path = Path.cwd() / ".holywater" / "holywater.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as conn:
        conn.executescript(SCHEMA)
        template_count = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
        fragment_count = conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]
        if force_seed or template_count == 0:
            conn.executemany(
                "INSERT INTO templates (style, mood, template, weight, enabled) VALUES (?, ?, ?, ?, ?)",
                TEMPLATES,
            )
        if force_seed or fragment_count == 0:
            conn.executemany(
                "INSERT INTO fragments (category, value, style, mood, weight) VALUES (?, ?, ?, ?, ?)",
                _all_fragments(),
            )
        conn.commit()
    return path


def _all_fragments() -> Iterable[tuple[str, str, str | None, str | None, float]]:
    yield from FRAGMENTS
    for fragments in CONTEXT_FRAGMENTS.values():
        yield from fragments


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert SQLite rows to plain dictionaries for easier weighting logic."""

    return [dict(row) for row in rows]
