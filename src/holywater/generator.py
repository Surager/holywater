"""Core text generation logic for the Holy Water project."""

from __future__ import annotations

import hashlib
import random
import re
from contextlib import closing
from datetime import date
from pathlib import Path
from string import Formatter
from typing import Any

from .db import connect, initialize_database, rows_to_dicts
from .models import HolyText

ALLOWED_STYLES = {"genesis", "psalm", "proverb", "revelation", "gospel", "commandment"}
ALLOWED_MOODS = {"serious", "absurd"}
RANDOM_VALUE = "random"
PLACEHOLDER_RE = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")

CONTEXT_KEYWORDS = {
    "home": ("清晨", "窗边", "厨房", "茶几", "家中", "院中"),
    "walk": ("路上", "街角", "行路", "风中", "树影", "门前"),
    "rest": ("午后", "榻边", "安静", "歇息", "灯下", "片刻"),
    "reading": ("书页", "灯下", "案头", "书桌", "窗前", "纸页"),
    "coding": ("代码", "终端", "调试", "异常", "缓存"),
    "thesis": ("论文", "脚注", "段落", "修订", "截止日期"),
    "gaming": ("排位", "加载", "复活", "显卡", "战场"),
}
MODERN_CONTEXTS = {"coding", "thesis", "gaming"}
MODERN_CONTEXT_KEYWORDS = tuple(
    keyword for context, keywords in CONTEXT_KEYWORDS.items() if context in MODERN_CONTEXTS for keyword in keywords
) + (
    "键盘",
    "标签",
    "窗口",
    "滚动条",
    "低电量",
    "提交",
    "构建",
    "堆栈",
    "查重",
    "格式",
    "参考文献",
    "战绩",
    "闪现",
    "小地图",
    "团战",
    "连败",
    "屏幕",
    "进度条",
    "番茄钟",
    "日志",
    "分支",
    "错误信息",
    "空指针",
    "断点",
    "摘要",
    "结论",
    "注释",
    "待办",
    "提醒事项",
    "匹配",
    "键位",
    "任务",
    "操作",
    "心态",
    "鼠标",
    "论证",
    "打印机",
    "通知",
    "白板",
    "便签",
    "消息",
    "日程表",
)
DEFAULT_CONTEXT_CHOICES = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    "home",
    "home",
    "home",
    "home",
    "walk",
    "walk",
    "rest",
    "rest",
    "reading",
    "reading",
]
DEFAULT_MOOD_CHOICES = ["serious", "serious", "serious", "serious", "serious", "absurd", "absurd"]
DEFAULT_INTENSITY_CHOICES = [1, 1, 2, 2, 3, 3, 4, 5]


class HolyWaterGenerator:
    """Generate biblical-style hydration reminders from SQLite templates."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = initialize_database(db_path)

    def generate(
        self,
        style: str = RANDOM_VALUE,
        mood: str = RANDOM_VALUE,
        intensity: int | None = None,
        context: str | None = RANDOM_VALUE,
        seed: int | str | None = None,
        *,
        save_history: bool = True,
        avoid_recent: bool = True,
    ) -> HolyText:
        """Return one generated HolyText.

        Args:
            style: One of genesis, psalm, proverb, revelation, gospel, commandment, or random.
            mood: serious, absurd, or random.
            intensity: 1..5, where higher values prefer stranger and stronger wording. None means random.
            context: Optional scene such as coding, thesis, gaming, or random.
            seed: Optional reproducibility seed.
            save_history: Store generated content in generation_history.
            avoid_recent: Retry a few times when generated content was seen recently.
        """
        seed_value = self._normalize_seed(seed)
        rng = random.Random(seed_value)
        style, mood, intensity, context = self._resolve_options(style, mood, intensity, context, rng)

        recent_texts = self._recent_texts(style, mood) if avoid_recent else set()
        last_candidate: HolyText | None = None

        for _ in range(12):
            candidate = self._generate_once(style, mood, intensity, context, seed_value, rng)
            last_candidate = candidate
            if candidate.content not in recent_texts:
                if save_history:
                    self._save_history(candidate.content, style, mood)
                return candidate

        # If the database is tiny, returning a repeat is better than failing.
        assert last_candidate is not None
        if save_history:
            self._save_history(last_candidate.content, style, mood)
        return last_candidate

    def daily(
        self,
        style: str = RANDOM_VALUE,
        mood: str = RANDOM_VALUE,
        intensity: int | None = None,
        context: str | None = RANDOM_VALUE,
        on_date: date | None = None,
    ) -> HolyText:
        """Return a deterministic daily text using the calendar date as seed."""

        day = on_date or date.today()
        seed = stable_seed(f"{day.isoformat()}:{style}:{mood}:{intensity}:{context or ''}")
        return self.generate(
            style=style,
            mood=mood,
            intensity=intensity,
            context=context,
            seed=seed,
            save_history=False,
            avoid_recent=False,
        )

    def _generate_once(
        self,
        style: str,
        mood: str,
        intensity: int,
        context: str | None,
        seed_value: int,
        rng: random.Random,
    ) -> HolyText:
        template = self._choose_template(style, mood, intensity, context, rng)
        categories = _template_fields(template["template"])
        values = {
            category: self._choose_fragment(category, style, mood, intensity, context, rng)
            for category in categories
        }
        content = Formatter().vformat(template["template"], (), values)
        reference = self._make_reference(style, intensity, rng)
        return HolyText(content=content, reference=reference, style=style, mood=mood, seed=seed_value)

    def _choose_template(
        self,
        style: str,
        mood: str,
        intensity: int,
        context: str | None,
        rng: random.Random,
    ) -> dict[str, Any]:
        with closing(connect(self.db_path)) as conn:
            rows = rows_to_dicts(
                conn.execute(
                    """
                    SELECT id, style, mood, template, weight
                    FROM templates
                    WHERE enabled = 1
                      AND style = ?
                      AND mood = ?
                    """,
                    (style, mood),
                )
            )
            if not rows:
                rows = rows_to_dicts(
                    conn.execute(
                        "SELECT id, style, mood, template, weight FROM templates WHERE enabled = 1"
                    )
                )
        if not rows:
            raise RuntimeError("No enabled templates found. Run `holywater init-db` first.")

        rows = _filter_context_rows(rows, context)
        weighted = [
            (row, _adjust_weight(row, style, mood, intensity, context, is_template=True))
            for row in rows
        ]
        return _weighted_choice(weighted, rng)

    def _choose_fragment(
        self,
        category: str,
        style: str,
        mood: str,
        intensity: int,
        context: str | None,
        rng: random.Random,
    ) -> str:
        with closing(connect(self.db_path)) as conn:
            rows = rows_to_dicts(
                conn.execute(
                    """
                    SELECT id, category, value, style, mood, weight
                    FROM fragments
                    WHERE category = ?
                      AND (style IS NULL OR style = ?)
                      AND (mood IS NULL OR mood = ?)
                    """,
                    (category, style, mood),
                )
            )
            if not rows:
                rows = rows_to_dicts(
                    conn.execute(
                        "SELECT id, category, value, style, mood, weight FROM fragments WHERE category = ?",
                        (category,),
                    )
                )
        if not rows:
            raise RuntimeError(f"No fragments found for category `{category}`.")

        rows = _filter_context_rows(rows, context)
        weighted = [(row, _adjust_weight(row, style, mood, intensity, context)) for row in rows]
        return _weighted_choice(weighted, rng)["value"]

    def _recent_texts(self, style: str, mood: str) -> set[str]:
        with closing(connect(self.db_path)) as conn:
            rows = conn.execute(
                """
                SELECT text
                FROM generation_history
                WHERE style = ?
                  AND mood = ?
                  AND created_at >= datetime('now', '-2 hours')
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (style, mood),
            ).fetchall()
        return {row["text"] for row in rows}

    def _save_history(self, text: str, style: str, mood: str) -> None:
        with closing(connect(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO generation_history (text, style, mood) VALUES (?, ?, ?)",
                (text, style, mood),
            )
            conn.commit()

    def _make_reference(self, style: str, intensity: int, rng: random.Random) -> str:
        book_by_style = {
            "genesis": "饮水记",
            "psalm": "杯中诗",
            "proverb": "清泉箴言",
            "revelation": "启杯录",
            "gospel": "补水福音",
            "commandment": "饮水诫",
        }
        chapter = rng.randint(1, max(2, intensity + 1))
        verse = rng.randint(1, 6 + intensity * 5)
        return f"《{book_by_style[style]}》{chapter}:{verse}"

    @staticmethod
    def _validate_style(style: str) -> str:
        if style not in ALLOWED_STYLES:
            raise ValueError(f"style must be one of: {', '.join(sorted(ALLOWED_STYLES))}")
        return style

    @staticmethod
    def _validate_mood(mood: str) -> str:
        if mood not in ALLOWED_MOODS:
            raise ValueError(f"mood must be one of: {', '.join(sorted(ALLOWED_MOODS))}")
        return mood

    @staticmethod
    def _validate_intensity(intensity: int) -> int:
        if intensity < 1 or intensity > 5:
            raise ValueError("intensity must be between 1 and 5")
        return intensity

    @classmethod
    def _resolve_options(
        cls,
        style: str,
        mood: str,
        intensity: int | None,
        context: str | None,
        rng: random.Random,
    ) -> tuple[str, str, int, str | None]:
        style = style.lower()
        mood = mood.lower()
        if style == RANDOM_VALUE:
            style = rng.choice(sorted(ALLOWED_STYLES))
        else:
            style = cls._validate_style(style)

        if mood == RANDOM_VALUE:
            mood = rng.choice(DEFAULT_MOOD_CHOICES)
        else:
            mood = cls._validate_mood(mood)

        if intensity is None or intensity == 0:
            intensity = rng.choice(DEFAULT_INTENSITY_CHOICES)
        else:
            intensity = cls._validate_intensity(intensity)

        context_marker = context.lower() if isinstance(context, str) else context
        if context_marker == RANDOM_VALUE:
            context = rng.choice(DEFAULT_CONTEXT_CHOICES)
        elif context_marker in {"", "none", "null"}:
            context = None

        return style, mood, intensity, context

    @staticmethod
    def _normalize_seed(seed: int | str | None) -> int:
        if seed is None:
            return random.SystemRandom().randint(1, 2**31 - 1)
        if isinstance(seed, int):
            return seed
        if seed.isdecimal():
            return int(seed)
        return stable_seed(seed)


def generate(
    style: str = RANDOM_VALUE,
    mood: str = RANDOM_VALUE,
    intensity: int | None = None,
    context: str | None = RANDOM_VALUE,
    seed: int | str | None = None,
    db_path: str | Path | None = None,
) -> HolyText:
    """Convenience library function for one-off generation."""

    return HolyWaterGenerator(db_path).generate(
        style=style,
        mood=mood,
        intensity=intensity,
        context=context,
        seed=seed,
    )


def stable_seed(value: str) -> int:
    """Turn arbitrary text into a repeatable 31-bit integer seed."""

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % (2**31 - 1)


def _template_fields(template: str) -> list[str]:
    """Return placeholder names in first-seen order."""

    fields: list[str] = []
    for match in PLACEHOLDER_RE.finditer(template):
        name = match.group(1)
        if name not in fields:
            fields.append(name)
    return fields


def _weighted_choice(items: list[tuple[dict[str, Any], float]], rng: random.Random) -> dict[str, Any]:
    total = sum(max(weight, 0.001) for _, weight in items)
    needle = rng.uniform(0, total)
    upto = 0.0
    for item, weight in items:
        upto += max(weight, 0.001)
        if upto >= needle:
            return item
    return items[-1][0]


def _filter_context_rows(rows: list[dict[str, Any]], context: str | None) -> list[dict[str, Any]]:
    if context in MODERN_CONTEXTS:
        return rows
    filtered = [
        row
        for row in rows
        if not any(keyword in (row.get("value") or row.get("template") or "") for keyword in MODERN_CONTEXT_KEYWORDS)
    ]
    return filtered or rows


def _adjust_weight(
    row: dict[str, Any],
    style: str,
    mood: str,
    intensity: int,
    context: str | None,
    *,
    is_template: bool = False,
) -> float:
    """Apply style, mood, context, and intensity bias to a stored row weight."""

    weight = float(row.get("weight") or 1)
    row_style = row.get("style")
    row_mood = row.get("mood")
    text = row.get("value") or row.get("template") or ""

    if row_style == style:
        weight *= 1.35
    if row_mood == mood:
        weight *= 1.25

    # Higher intensity favors absurd, apocalyptic, and imperative language.
    if mood == "absurd":
        weight *= 0.8 + intensity * 0.22
    if style in {"revelation", "commandment"}:
        weight *= 0.9 + intensity * 0.12
    if any(token in text for token in ("不可", "起来", "第七", "末了", "兽", "诫命")):
        weight *= 0.85 + intensity * 0.16

    if context:
        if context not in MODERN_CONTEXTS and any(keyword in text for keyword in MODERN_CONTEXT_KEYWORDS):
            weight *= 0.01
        for other_context, keywords in CONTEXT_KEYWORDS.items():
            if other_context == context:
                continue
            if any(keyword in text for keyword in keywords):
                weight *= 0.12
                break
        for keyword in CONTEXT_KEYWORDS.get(context, (context,)):
            if keyword and keyword in text:
                weight *= 2.25
                break
        if is_template and "context_scene" in text:
            weight *= 1.0 + intensity * 0.05
    elif any(keyword in text for keyword in MODERN_CONTEXT_KEYWORDS):
        weight *= 0.01

    return weight
