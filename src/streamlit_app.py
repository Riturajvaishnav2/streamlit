import os
import sys

import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.core.config import APP_TITLE, DEFAULT_OPENAI_API_KEY
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
        api_key = st.text_input(
            "OpenAI API Key", type="password", value=DEFAULT_OPENAI_API_KEY
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

    _render_step_upload()
    _render_step_common_json(api_key, common_prompt_text)
    _render_step_pairs(api_key, common_prompt_text, pair_prompt_id, pair_prompt_text)
    _render_step_template_excel()


if __name__ == "__main__":
    main()
