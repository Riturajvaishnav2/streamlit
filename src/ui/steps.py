import json
import os
import tempfile
from typing import Tuple

import streamlit as st

from src.core.agreements import _agreements_from_common
from src.core.json_utils import _parse_json
from src.core.llm import _generate_common_json, _generate_pair_output
from src.core.qdrant import _qdrant_fetch_history, _qdrant_upsert_history
from src.core.state import _ensure_pair_outputs_size, _now_iso
from src.processing.excel import _output_to_excel_bytes, _output_to_template_excel_bytes
from src.processing.files import (
    _convert_with_docling,
    _read_upload_to_md,
    _read_upload_to_jsonl,
)
from src.ui.components import _display_pair_output


# Step 1: Upload and convert to Markdown.
def _render_step_upload() -> None:
    st.header("Step 1: Upload & Convert to Markdown")
    uploaded = st.file_uploader(
        "Upload source file",
        type=None,
        help="Upload any supported format. Docling handles conversion to Markdown/JSONL.",
    )
    if uploaded:
        upload_bytes = uploaded.getvalue()
        suffix = os.path.splitext(uploaded.name)[1]
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(upload_bytes)
                temp_path = temp_file.name
            md_text, jsonl_text, error = _convert_with_docling(temp_path)
            if error:
                st.warning(error)
                st.session_state.md_text = _read_upload_to_md(
                    uploaded, uploaded.name, uploaded.type, upload_bytes
                )
                st.session_state.jsonl_text = _read_upload_to_jsonl(
                    uploaded, uploaded.name, uploaded.type, upload_bytes
                )
                if not st.session_state.md_text:
                    st.info(
                        "Uploaded file appears to be binary. Install Docling to "
                        "convert it or upload a text-based file."
                    )
            else:
                st.session_state.md_text = md_text
                st.session_state.jsonl_text = jsonl_text
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    st.text_area("Markdown preview", st.session_state.md_text, height=200)
    if st.session_state.md_text:
        st.download_button(
            "Download Markdown",
            st.session_state.md_text,
            file_name="converted.md",
        )


# Step 2: Generate and edit Common JSON.
def _render_step_common_json(api_key: str, common_prompt_text: str) -> None:
    st.header("Step 2: Generate Common JSON")
    if st.button("Generate Common JSON"):
        st.session_state.common_json = _generate_common_json(
            api_key, common_prompt_text, st.session_state.md_text
        )
        st.session_state.pair_index = 0
        st.session_state.pair_outputs = []

    if st.session_state.common_json:
        st.subheader("Common JSON Output")
        st.json(st.session_state.common_json)

    agreements = _agreements_from_common(st.session_state.common_json)
    if agreements:
        st.subheader("Human-in-the-loop edits")
        agreements_json = json.dumps(agreements, indent=2)
        edited_text = st.text_area(
            "Edit agreements JSON array",
            agreements_json,
            height=300,
        )
        if st.button("Apply edits to JSON"):
            parsed = _parse_json(edited_text)
            if isinstance(parsed, list):
                st.session_state.common_json["agreements"] = parsed
                st.session_state.common_json.setdefault(
                    "metadata", {"source_filename": "DISCOUNT_IOT", "record_count": 0}
                )
                st.session_state.common_json["metadata"]["record_count"] = len(parsed)
                st.success("Updated agreements in JSON.")
            else:
                st.error("Edits must be a JSON array of agreements.")


# Step 3: Process each client-partner pair.
def _render_step_pairs(
    api_key: str,
    common_prompt_text: str,
    pair_prompt_id: str,
    pair_prompt_text: str,
) -> None:
    st.header("Step 3: Process Client–Partner Pairs")
    agreements = _agreements_from_common(st.session_state.common_json)
    if not agreements:
        st.info("Generate common JSON first to continue.")
        return

    _ensure_pair_outputs_size(agreements)
    total = len(agreements)
    idx = min(st.session_state.pair_index, total - 1)
    pair = agreements[idx]
    st.write(f"Processing pair {idx + 1} of {total}")
    st.json(pair)
    agreement_key = f"{pair.get('client','')}-{pair.get('partner','')}"

    col_left, col_right = st.columns([2, 1])
    with col_left:
        user_note = st.text_area(
            "Chat with LLM (regeneration notes)",
            st.session_state.pair_chat.get(idx, ""),
            height=100,
        )
        if st.session_state.pair_outputs[idx]:
            excel_bytes = _output_to_excel_bytes(st.session_state.pair_outputs[idx])
            st.download_button(
                "Download Excel",
                excel_bytes,
                file_name=f"pair_{idx + 1}_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("Generate output to enable Excel download.")
        with st.expander("Prompt history (Qdrant)"):
            history = _qdrant_fetch_history(agreement_key)
            if not history:
                st.info("No stored history or Qdrant not configured.")
            for item in history:
                st.write(
                    f"[{item.get('created_at','')}] "
                    f"{item.get('role','user')}: {item.get('content','')}"
                )
    with col_right:
        st.write("Actions")
        if st.button("Generate Pair Output"):
            st.session_state.pair_chat[idx] = user_note
            if user_note.strip():
                _qdrant_upsert_history(
                    api_key,
                    agreement_key,
                    pair_prompt_id,
                    "user",
                    user_note,
                )
            st.session_state.pair_outputs[idx] = _generate_pair_output(
                api_key, pair_prompt_text, pair, user_note
            )
        if st.button("Generate / Regenerate"):
            if not st.session_state.md_text:
                st.warning("Upload and convert a file before regenerating.")
            else:
                st.session_state.common_json = _generate_common_json(
                    api_key,
                    common_prompt_text,
                    st.session_state.md_text,
                    user_note,
                )
                st.session_state.pair_index = 0
                st.session_state.pair_outputs = []
                st.session_state.pair_chat = {}
                st.session_state.pair_template_excels = []
                st.rerun()
        if st.button("Save outputs"):
            st.session_state.pair_outputs[idx]["saved_at"] = _now_iso()
            try:
                st.session_state.pair_template_excels[idx] = _output_to_template_excel_bytes(
                    st.session_state.pair_outputs[idx]
                )
                st.success("Saved in session and prepared template output.")
            except Exception as exc:
                st.warning(f"Template export failed: {exc}")
        if st.session_state.pair_template_excels[idx]:
            st.download_button(
                "Download Template Excel",
                st.session_state.pair_template_excels[idx],
                file_name=f"pair_{idx + 1}_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    output = st.session_state.pair_outputs[idx]
    if output:
        _display_pair_output(output)

    st.divider()
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        if st.button("Previous") and idx > 0:
            st.session_state.pair_index = idx - 1
    with col_b:
        if st.button("Next") and idx < total - 1:
            st.session_state.pair_index = idx + 1
    with col_c:
        if st.button("Reset Workflow"):
            st.session_state.common_json = {}
            st.session_state.pair_outputs = []
            st.session_state.pair_index = 0
            st.session_state.pair_chat = {}
            st.session_state.pair_template_excels = []


# Step 4: Template-mapped Excel download.
def _render_step_template_excel() -> None:
    st.header("Step 4: Template-Mapped Excel")
    idx = st.session_state.pair_index
    if st.session_state.pair_template_excels[idx]:
        st.download_button(
            "Download Template Excel",
            st.session_state.pair_template_excels[idx],
            file_name=f"pair_{idx + 1}_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("Save outputs to generate the template-mapped Excel.")
