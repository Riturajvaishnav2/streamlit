import io
import json
import os
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.core.json_utils import _parse_json, _to_jsonl


# Heuristic to detect text-like binary payloads.
def _looks_like_text(data: bytes) -> bool:
    if not data:
        return True
    if b"\x00" in data:
        return False
    sample = data[:2048]
    non_printable = sum(1 for b in sample if b < 9 or (13 < b < 32))
    return non_printable / max(len(sample), 1) < 0.05


# Decide whether an upload should be treated as text.
def _is_text_upload(filename: str, mime_type: str, data: bytes) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    text_exts = {
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".xml",
        ".html",
        ".htm",
        ".rst",
        ".log",
        ".py",
        ".sql",
    }
    if ext in text_exts:
        return True
    if mime_type and mime_type.startswith("text/"):
        return True
    return _looks_like_text(data)


# Remove fully empty rows/columns while preserving data-heavy sheets.
def _drop_empty_rows_cols(df: pd.DataFrame) -> pd.DataFrame:
    def _has_value(value: Any) -> bool:
        if value is None or pd.isna(value):
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True

    def _row_has_value(row: pd.Series) -> bool:
        return any(_has_value(value) for value in row)

    def _col_has_value(col: pd.Series) -> bool:
        return any(_has_value(value) for value in col)

    row_mask = df.apply(_row_has_value, axis=1)
    col_mask = df.apply(_col_has_value, axis=0)
    if row_mask.any():
        df = df.loc[row_mask]
    if col_mask.any():
        df = df.loc[:, col_mask]
    return df


# Render a DataFrame as Markdown, dropping empty rows/columns.
def _df_to_markdown(df: pd.DataFrame) -> str:
    # Simple Markdown table renderer to avoid extra dependencies.
    def _cell(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        text = str(value)
        return text.replace("|", "\\|")

    if df.empty:
        return ""

    df = _drop_empty_rows_cols(df)
    if df.empty or df.shape[1] == 0:
        return ""

    if isinstance(df.columns, pd.RangeIndex):
        headers = [f"Column {idx + 1}" for idx in range(len(df.columns))]
    else:
        headers = [str(col) for col in df.columns.tolist()]
    header_row = "| " + " | ".join(_cell(h) for h in headers) + " |"
    divider_row = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = [
        "| " + " | ".join(_cell(value) for value in row) + " |"
        for row in df.itertuples(index=False)
    ]
    return "\n".join([header_row, divider_row, *data_rows])


# Convert CSV/TSV/XLSX content into Markdown tables.
def _tabular_bytes_to_markdown(filename: str, raw: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".csv", ".tsv"}:
        try:
            sep = "\t" if ext == ".tsv" else ","
            df = pd.read_csv(io.BytesIO(raw), sep=sep)
            return _df_to_markdown(df)
        except Exception:
            return ""
    if ext in {".xlsx", ".xlsm", ".xls"}:
        try:
            sheets = pd.read_excel(io.BytesIO(raw), sheet_name=None, header=None)
            sections = []
            for sheet_name, df in sheets.items():
                table = _df_to_markdown(df)
                if not table:
                    continue
                sections.append(f"## Sheet: {sheet_name}\n{table}")
            return "\n\n".join(sections)
        except Exception:
            return ""
    return ""


# Convert CSV/TSV/XLSX content into JSONL.
def _tabular_bytes_to_jsonl(filename: str, raw: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".csv", ".tsv"}:
        try:
            sep = "\t" if ext == ".tsv" else ","
            df = pd.read_csv(io.BytesIO(raw), sep=sep)
            df = _drop_empty_rows_cols(df)
            return _to_jsonl(df.to_dict(orient="records"))
        except Exception:
            return ""
    if ext in {".xlsx", ".xlsm", ".xls"}:
        try:
            sheets = pd.read_excel(io.BytesIO(raw), sheet_name=None, header=None)
            payload = {
                name: _drop_empty_rows_cols(sheet).to_dict(orient="records")
                for name, sheet in sheets.items()
            }
            return _to_jsonl(payload)
        except Exception:
            return ""
    return ""


# Best-effort Markdown extraction for non-Docling flows.
def _read_upload_to_md(
    uploaded_file: Optional[Any],
    filename: str,
    mime_type: str,
    raw: bytes,
) -> str:
    if not uploaded_file:
        return ""
    tabular_md = _tabular_bytes_to_markdown(filename, raw)
    if tabular_md:
        return tabular_md
    if not _is_text_upload(filename, mime_type, raw):
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return ""


# Best-effort JSONL extraction for non-Docling flows.
def _read_upload_to_jsonl(
    uploaded_file: Optional[Any],
    filename: str,
    mime_type: str,
    raw: bytes,
) -> str:
    if not uploaded_file:
        return ""
    tabular_jsonl = _tabular_bytes_to_jsonl(filename, raw)
    if tabular_jsonl:
        return tabular_jsonl
    if not _is_text_upload(filename, mime_type, raw):
        return ""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ""
    parsed = _parse_json(text)
    if parsed:
        return _to_jsonl(parsed)
    return ""


# Convert via Docling if installed, returning Markdown + JSONL.
def _convert_with_docling(file_path: str) -> Tuple[str, str, str]:
    try:
        from docling.document_converter import DocumentConverter
    except Exception:
        return "", "", "Docling is not installed. Install docling to enable conversion."

    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        document = result.document
        md_text = document.export_to_markdown()
        json_data = document.export_to_json()
        jsonl_text = _to_jsonl(json_data)
        return md_text, jsonl_text, ""
    except Exception as exc:
        return "", "", f"Docling conversion failed: {exc}"
