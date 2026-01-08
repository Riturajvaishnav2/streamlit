import os
import sys

import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.core.config import (
    APP_TITLE,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LOCAL_LLM_API_KEY,
    DEFAULT_LOCAL_LLM_BASE_URL,
    DEFAULT_LOCAL_LLM_MODEL,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENAI_API_KEY,
    DEFAULT_OPENAI_MODEL,
)
from src.core.qdrant import _qdrant_status
from src.core.state import _init_state
from src.ui.components import _render_prompt_manager
from src.ui.steps import (
    _render_step_common_json,
    _render_step_pairs,
    _render_step_template_excel,
    _render_step_upload,
)


# Main Streamlit app entrypoint.
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    _init_state()

    with st.sidebar:
        st.header("Configuration")
        provider_default = DEFAULT_LLM_PROVIDER.strip().lower()
        if provider_default not in {"openai", "local", "ollama"}:
            provider_default = "openai"
        if provider_default == "openai":
            provider_label_default = "OpenAI"
        elif provider_default == "ollama":
            provider_label_default = "Ollama (local)"
        else:
            provider_label_default = "Local (OpenAI-compatible)"
        if st.session_state.get("llm_provider_env") != provider_default:
            st.session_state.llm_provider = provider_label_default
            st.session_state.llm_provider_env = provider_default
        provider_index = {"OpenAI": 0, "Local (OpenAI-compatible)": 1, "Ollama (local)": 2}
        provider_label = st.selectbox(
            "LLM Provider",
            ["OpenAI", "Local (OpenAI-compatible)", "Ollama (local)"],
            index=provider_index.get(provider_label_default, 0),
            key="llm_provider",
        )
        if provider_label == "OpenAI":
            provider = "openai"
            api_key = st.text_input(
                "OpenAI API Key", type="password", value=DEFAULT_OPENAI_API_KEY
            )
            model_name = st.text_input("OpenAI Model", value=DEFAULT_OPENAI_MODEL)
            base_url = ""
        elif provider_label == "Ollama (local)":
            provider = "ollama"
            api_key = ""
            base_url = st.text_input(
                "Ollama Base URL",
                value=DEFAULT_OLLAMA_BASE_URL,
            )
            model_name = st.text_input(
                "Ollama Model",
                value=DEFAULT_OLLAMA_MODEL,
            )
        else:
            provider = "local"
            api_key = st.text_input(
                "Local API Key (optional)",
                type="password",
                value=DEFAULT_LOCAL_LLM_API_KEY,
            )
            base_url = st.text_input(
                "Local Base URL",
                value=DEFAULT_LOCAL_LLM_BASE_URL,
            )
            model_name = st.text_input(
                "Local Model",
                value=DEFAULT_LOCAL_LLM_MODEL,
            )
        st.divider()
        st.subheader("Common JSON Prompt")
        _, common_prompt_text = _render_prompt_manager(
            "Select prompt version",
            "common_prompt_versions",
            "active_common_prompt_id",
        )
        st.divider()
        st.subheader("Pair Generation Prompt")
        pair_prompt_id, pair_prompt_text = _render_prompt_manager(
            "Select pair prompt version",
            "pair_prompt_versions",
            "active_pair_prompt_id",
        )
        st.divider()
        st.subheader("Qdrant Status")
        st.caption(
            "History storage uses OpenAI embeddings; set OPENAI_API_KEY to enable."
        )
        if st.button("Check Qdrant"):
            st.json(_qdrant_status())

    _render_step_upload()
    _render_step_common_json(
        provider,
        api_key,
        model_name,
        base_url,
        common_prompt_text,
    )
    _render_step_pairs(
        provider,
        api_key,
        model_name,
        base_url,
        common_prompt_text,
        pair_prompt_id,
        pair_prompt_text,
    )
    _render_step_template_excel()


if __name__ == "__main__":
    main()
