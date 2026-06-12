"""Shared data models used by library, CLI, and API modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Style = Literal["genesis", "psalm", "proverb", "revelation", "gospel", "commandment"]
Mood = Literal["serious", "absurd"]


@dataclass(frozen=True)
class HolyText:
    """Generated hydration reminder returned by the public library API."""

    content: str
    reference: str
    style: str
    mood: str
    seed: int
