"""Example library-mode usage.

Run from the repository root:
    python examples/example_usage.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from holywater import HolyWaterGenerator, generate


def main() -> None:
    one = generate(style="psalm", mood="serious", intensity=2, context="coding", seed=20260612)
    print(f"{one.content} {one.reference}")

    generator = HolyWaterGenerator()
    daily = generator.daily(style="revelation", mood="absurd", intensity=5, context="gaming")
    print(f"{daily.content} {daily.reference}")


if __name__ == "__main__":
    main()
