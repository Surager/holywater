"""FastAPI application for API mode."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

from .db import initialize_database
from .generator import HolyWaterGenerator

app = FastAPI(
    title="Holy Water API",
    description="Biblical-style hydration reminder generator.",
    version="0.1.0",
)


class HolyTextResponse(BaseModel):
    """JSON representation of a generated reminder."""

    content: str
    reference: str
    style: str
    mood: str
    seed: int


def _generator() -> HolyWaterGenerator:
    db_path = os.getenv("HOLYWATER_DB")
    return HolyWaterGenerator(Path(db_path) if db_path else None)


@app.on_event("startup")
def startup() -> None:
    """Ensure the SQLite database exists before handling requests."""

    db_path = os.getenv("HOLYWATER_DB")
    initialize_database(Path(db_path) if db_path else None)


@app.get("/generate", response_model=HolyTextResponse)
def generate_endpoint(
    style: str = Query("genesis", description="genesis, psalm, proverb, revelation, gospel, commandment"),
    mood: str = Query("serious", description="serious or absurd"),
    intensity: int = Query(3, ge=1, le=5),
    context: Optional[str] = Query(None, description="Optional context, e.g. coding, thesis, gaming"),
    seed: Optional[str] = Query(None, description="Optional reproducibility seed"),
) -> HolyTextResponse:
    """Generate one reminder and write it to generation_history."""

    text = _generator().generate(style=style, mood=mood, intensity=intensity, context=context, seed=seed)
    return HolyTextResponse(**text.__dict__)


@app.get("/daily", response_model=HolyTextResponse)
def daily_endpoint(
    style: str = Query("genesis", description="genesis, psalm, proverb, revelation, gospel, commandment"),
    mood: str = Query("serious", description="serious or absurd"),
    intensity: int = Query(3, ge=1, le=5),
    context: Optional[str] = Query(None, description="Optional context, e.g. coding, thesis, gaming"),
    day: Optional[date] = Query(None, description="Date used as daily seed. Defaults to today."),
) -> HolyTextResponse:
    """Return a deterministic daily reminder for the given date."""

    text = _generator().daily(
        style=style,
        mood=mood,
        intensity=intensity,
        context=context,
        on_date=day or date.today(),
    )
    return HolyTextResponse(**text.__dict__)
