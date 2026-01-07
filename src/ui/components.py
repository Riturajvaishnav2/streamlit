from typing import Dict, Tuple

import streamlit as st

from src.core.state import _now_iso


# UI for managing prompt versions.
def _render_prompt_manager(
    label: str,
    versions_key: str,
    active_key: str,
) -> Tuple[str, str]:
    versions = st.session_state[versions_key]
    options = {f"{v['id']} - {v['name']}": v["id"] for v in versions}
    selected_label = st.selectbox(
        label, list(options.keys()), key=f"{versions_key}_select_prompt"
    )
    selected_id = options[selected_label]
    st.session_state[active_key] = selected_id
    active_prompt = next(v["prompt"] for v in versions if v["id"] == selected_id)
    edited_prompt = st.text_area(
        "Prompt template",
        active_prompt,
        height=200,
        key=f"{versions_key}_prompt_template",
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        new_name = st.text_input(
            "New version name",
            value=f"{selected_id} copy",
            key=f"{versions_key}_new_version_name",
        )
    with col_b:
        if st.button("Save new version", key=f"{versions_key}_save_new_version"):
            new_id = f"v{len(versions) + 1}"
            versions.append(
                {
                    "id": new_id,
                    "name": new_name,
                    "prompt": edited_prompt,
                    "created_at": _now_iso(),
                }
            )
            st.session_state[active_key] = new_id
            st.success(f"Saved {new_id}")
    return selected_id, edited_prompt


# Show output JSON in the UI.
def _display_pair_output(output: Dict[str, object]) -> None:
    st.subheader("Generated Output JSON")
    st.json(output)
