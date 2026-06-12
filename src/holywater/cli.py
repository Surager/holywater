"""Typer command line interface for Holy Water."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .db import initialize_database
from .generator import HolyWaterGenerator

app = typer.Typer(help="Generate biblical-style hydration reminders.")


@app.command("init-db")
def init_db(
    db_path: Optional[Path] = typer.Option(
        None,
        "--db",
        help="SQLite database path. Defaults to ~/.holywater/holywater.sqlite3.",
    ),
    force_seed: bool = typer.Option(False, help="Insert bundled examples even if tables already contain rows."),
) -> None:
    """Create SQLite tables and seed example templates/fragments."""

    path = initialize_database(db_path, force_seed=force_seed)
    typer.echo(f"Database initialized: {path}")


@app.command()
def generate(
    style: str = typer.Option("genesis", help="genesis, psalm, proverb, revelation, gospel, commandment."),
    mood: str = typer.Option("serious", help="serious or absurd."),
    intensity: int = typer.Option(3, min=1, max=5, help="1..5, from gentle to apocalyptic."),
    context: Optional[str] = typer.Option(None, help="Optional context, e.g. coding, thesis, gaming."),
    seed: Optional[str] = typer.Option(None, help="Optional seed for reproducible output."),
    db_path: Optional[Path] = typer.Option(None, "--db", help="SQLite database path."),
    json_output: bool = typer.Option(False, "--json", help="Print structured JSON."),
) -> None:
    """Generate one reminder and store it in generation_history."""

    text = HolyWaterGenerator(db_path).generate(
        style=style,
        mood=mood,
        intensity=intensity,
        context=context,
        seed=seed,
    )
    if json_output:
        typer.echo(json.dumps(text.__dict__, ensure_ascii=False, indent=2))
        return
    typer.echo(f"{text.content} {text.reference}")


@app.command()
def daily(
    style: str = typer.Option("genesis", help="genesis, psalm, proverb, revelation, gospel, commandment."),
    mood: str = typer.Option("serious", help="serious or absurd."),
    intensity: int = typer.Option(3, min=1, max=5, help="1..5, from gentle to apocalyptic."),
    context: Optional[str] = typer.Option(None, help="Optional context, e.g. coding, thesis, gaming."),
    db_path: Optional[Path] = typer.Option(None, "--db", help="SQLite database path."),
    json_output: bool = typer.Option(False, "--json", help="Print structured JSON."),
) -> None:
    """Generate the deterministic text for today."""

    text = HolyWaterGenerator(db_path).daily(
        style=style,
        mood=mood,
        intensity=intensity,
        context=context,
    )
    if json_output:
        typer.echo(json.dumps(text.__dict__, ensure_ascii=False, indent=2))
        return
    typer.echo(f"{text.content} {text.reference}")


if __name__ == "__main__":
    app()
