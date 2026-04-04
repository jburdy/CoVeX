#!/usr/bin/env python3
"""
Extract Mermaid blocks from Markdown files and render them as PNG files.

Execution from the repository root:
- `uv run --project backend python tools/validation/render_mermaid_pngs.py`
- Always renders diagrams from `CoVeX-1-rapport.md` and `CoVeX-2-annexes.md`.
- `--output-dir` overrides the root destination directory.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATHS = [
    ROOT_DIR / "rapport" / "CoVeX-1-rapport.md",
    ROOT_DIR / "rapport" / "CoVeX-2-annexes.md",
]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "rapport" / "artifacts" / "mermaid"

MERMAID_BLOCK_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
VISUAL_ID_RE = re.compile(r"id:\s*([A-Za-z0-9_-]+)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
NON_SLUG_RE = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class MermaidDiagram:
    index: int
    stem: str
    content: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render all Mermaid blocks from the CoVeX report and annexes into PNG files."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Root directory that will receive per-document PNG folders (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=2.0,
        help="Scale factor passed to mermaid-cli for higher-resolution PNGs.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    value = value.replace("’", "-").replace("'", "-")
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    lowered = normalized.strip().lower().replace(" ", "-")
    slug = NON_SLUG_RE.sub("-", lowered)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "diagram"


def find_diagram_stem(preceding_text: str, index: int) -> str:
    visual_ids = VISUAL_ID_RE.findall(preceding_text[-1200:])
    if visual_ids:
        return slugify(visual_ids[-1])

    headings = HEADING_RE.findall(preceding_text)
    if headings:
        return slugify(headings[-1])

    return f"diagram-{index:02d}"


def build_diagrams(markdown: str) -> list[MermaidDiagram]:
    diagrams: list[MermaidDiagram] = []
    for index, match in enumerate(MERMAID_BLOCK_RE.finditer(markdown), start=1):
        preceding_text = markdown[: match.start()]
        diagrams.append(
            MermaidDiagram(
                index=index,
                stem=find_diagram_stem(preceding_text, index),
                content=match.group(1).strip(),
            )
        )
    return diagrams


def render_diagram(diagram: MermaidDiagram, output_dir: Path, scale: float) -> Path:
    output_path = output_dir / f"{diagram.stem}.png"
    with tempfile.TemporaryDirectory(
        prefix=f"mermaid_{diagram.index:02d}_"
    ) as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"{diagram.stem}.mmd"
        input_path.write_text(f"{diagram.content}\n", encoding="utf-8")

        command = [
            "npx",
            "-y",
            "@mermaid-js/mermaid-cli",
            "-i",
            str(input_path),
            "-o",
            str(output_path),
            "-s",
            str(scale),
            "-b",
            "white",
        ]
        subprocess.run(command, check=True)
    return output_path


def render_markdown_file(input_path: Path, output_root: Path, scale: float) -> int:
    markdown = input_path.read_text(encoding="utf-8")
    diagrams = build_diagrams(markdown)
    if not diagrams:
        raise SystemExit(f"No Mermaid block found in: {input_path}")

    output_dir = output_root / input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing_png in output_dir.glob("*.png"):
        existing_png.unlink()

    print(f"Source: {input_path}")
    print(f"Output: {output_dir}")
    print(f"Diagrams: {len(diagrams)}")

    for diagram in diagrams:
        output_path = render_diagram(diagram, output_dir, scale)
        print(f"[{diagram.index}/{len(diagrams)}] {output_path.name}")

    return len(diagrams)


def main() -> int:
    args = parse_args()
    input_paths = [path.resolve() for path in DEFAULT_INPUT_PATHS]
    output_dir = args.output_dir.resolve()

    if shutil.which("npx") is None:
        raise SystemExit("`npx` is required but was not found in PATH.")

    for input_path in input_paths:
        if not input_path.exists():
            raise SystemExit(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    total_count = 0
    for input_path in input_paths:
        total_count += render_markdown_file(input_path, output_dir, args.scale)
        print()

    print(f"Rendered {total_count} diagram(s) from {len(input_paths)} file(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
