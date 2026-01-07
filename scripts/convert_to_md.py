#!/usr/bin/env python3
import argparse
import os
import sys


def _convert_with_docling(file_path: str) -> str:
    try:
        from docling.document_converter import DocumentConverter
    except Exception as exc:
        raise RuntimeError(
            "Docling is not installed. Install it with `pip install docling`."
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert any file to Markdown using Docling."
    )
    parser.add_argument("input", help="Path to the input file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output Markdown file. Defaults to stdout.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        md_text = _convert_with_docling(args.input)
    except Exception as exc:
        print(f"Docling conversion failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(md_text)
    else:
        sys.stdout.write(md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
