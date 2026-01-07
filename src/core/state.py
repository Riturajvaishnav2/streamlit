from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from src.core.config import DEFAULT_COMMON_PROMPT, DEFAULT_PAIR_PROMPT


# UTC timestamp used for history metadata.
def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# Initialize Streamlit session state for the workflow.
def _init_state() -> None:
    if "md_text" not in st.session_state:
        st.session_state.md_text = ""
    if "jsonl_text" not in st.session_state:
        st.session_state.jsonl_text = ""
    if "common_prompt_versions" not in st.session_state:
        st.session_state.common_prompt_versions = [
            {
                "id": "v1",
                "name": "Default v1",
                "prompt": DEFAULT_COMMON_PROMPT,
                "created_at": _now_iso(),
            }
        ]
    if "pair_prompt_versions" not in st.session_state:
        st.session_state.pair_prompt_versions = [
            {
                "id": "v1",
                "name": "Default v1",
                "prompt": DEFAULT_PAIR_PROMPT,
                "created_at": _now_iso(),
            }
        ]
    if "active_common_prompt_id" not in st.session_state:
        st.session_state.active_common_prompt_id = "v1"
    if "active_pair_prompt_id" not in st.session_state:
        st.session_state.active_pair_prompt_id = "v1"
    if "common_json" not in st.session_state:
        st.session_state.common_json = {}
    if "pair_index" not in st.session_state:
        st.session_state.pair_index = 0
    if "pair_outputs" not in st.session_state:
        st.session_state.pair_outputs = []
    if "pair_template_excels" not in st.session_state:
        st.session_state.pair_template_excels = []
    if "pair_chat" not in st.session_state:
        st.session_state.pair_chat = {}


# Make sure per-pair output and template buffers match agreement count.
def _ensure_pair_outputs_size(agreements: List[Dict[str, Any]]) -> None:
    outputs = st.session_state.pair_outputs
    if len(outputs) < len(agreements):
        outputs.extend([{} for _ in range(len(agreements) - len(outputs))])
    st.session_state.pair_outputs = outputs
    templates = st.session_state.pair_template_excels
    if len(templates) < len(agreements):
        templates.extend([b"" for _ in range(len(agreements) - len(templates))])
    st.session_state.pair_template_excels = templates
