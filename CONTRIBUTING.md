# Contributing

## Development

```powershell
uv sync
uv run python tests/test_generator.py
```

Before submitting changes, run:

```powershell
uv run python -B -c "import pathlib; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for root in ('src','examples','tests') for p in pathlib.Path(root).rglob('*.py')]; print('Syntax check passed.')"
uv run python tests/test_generator.py
```

## Corpus Contributions

Do not copy modern Bible translations, devotional notes, or copyrighted source
text into the database. Add templates and fragments as original or clearly
human-rewritten text inspired by public-domain or permissively licensed
structures.

For corpus changes, include the source category and licensing rationale in the
pull request description.

## Code Style

Keep changes scoped, prefer standard-library solutions, and add tests for
behavioral changes.
