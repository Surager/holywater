"""FastAPI application for API mode."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, Query, Request
from pydantic import BaseModel

from .db import initialize_database
from .generator import HolyWaterGenerator

StyleParam = Literal["random", "genesis", "psalm", "proverb", "revelation", "gospel", "commandment"]
MoodParam = Literal["random", "serious", "absurd"]
ContextParam = Literal[
    "random",
    "home",
    "walk",
    "rest",
    "reading",
    "meal",
    "garden",
    "coding",
    "thesis",
    "gaming",
    "none",
]


class HolyTextResponse(BaseModel):
    """JSON representation of a generated reminder."""

    content: str
    reference: str
    style: str
    mood: str
    seed: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared API state once per process."""

    db_path = os.getenv("HOLYWATER_DB")
    initialize_database(Path(db_path) if db_path else None)
    app.state.generator = _build_generator()
    yield


app = FastAPI(
    title="Holy Water API",
    description="Biblical-style hydration reminder generator.",
    version="0.1.0",
    lifespan=lifespan,
)


def _build_generator() -> HolyWaterGenerator:
    db_path = os.getenv("HOLYWATER_DB")
    return HolyWaterGenerator(Path(db_path) if db_path else None)


@app.get("/generate", response_model=HolyTextResponse)
def generate_endpoint(
    request: Request,
    style: StyleParam = Query("random", description="random, genesis, psalm, proverb, revelation, gospel, commandment"),
    mood: MoodParam = Query("random", description="random, serious, or absurd"),
    intensity: Optional[int] = Query(None, ge=1, le=5, description="Random by default. Use 1..5 to fix intensity."),
    context: ContextParam = Query(
        "random",
        description="random by default, or use home, walk, rest, reading, meal, garden, coding, thesis, gaming, none",
    ),
    seed: Optional[str] = Query(None, description="Optional reproducibility seed"),
) -> HolyTextResponse:
    """Generate one reminder and write it to generation_history."""

    text = request.app.state.generator.generate(style=style, mood=mood, intensity=intensity, context=context, seed=seed)
    return HolyTextResponse(**text.__dict__)


@app.get("/daily", response_model=HolyTextResponse)
def daily_endpoint(
    request: Request,
    style: StyleParam = Query("random", description="random, genesis, psalm, proverb, revelation, gospel, commandment"),
    mood: MoodParam = Query("random", description="random, serious, or absurd"),
    intensity: Optional[int] = Query(None, ge=1, le=5, description="Random by default. Use 1..5 to fix intensity."),
    context: ContextParam = Query(
        "random",
        description="random by default, or use home, walk, rest, reading, meal, garden, coding, thesis, gaming, none",
    ),
    day: Optional[date] = Query(None, description="Date used as daily seed. Defaults to today."),
) -> HolyTextResponse:
    """Return a deterministic daily reminder for the given date."""

    text = request.app.state.generator.daily(
        style=style,
        mood=mood,
        intensity=intensity,
        context=context,
        on_date=day or date.today(),
    )
    return HolyTextResponse(**text.__dict__)
