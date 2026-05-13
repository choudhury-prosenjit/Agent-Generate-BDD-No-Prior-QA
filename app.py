"""Streamlit UI for the BDD Test Case Generator."""

import io
import os
import zipfile

from dotenv import load_dotenv
import streamlit as st

from src.github_fetcher import fetch_repository_code, parse_github_url
from src.bdd_generator import generate_bdd_tests

# ── Load environment variables ───────────────────────────────────────────────
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY", "")
github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GIT_HUB_TOKEN")

# ── Page configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="BDD Test Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .stTextInput > label { font-weight: 600; }
    .block-container { padding-top: 2rem; }
    /* Hide the top bar (Deploy button / toolbar) */
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Main area ────────────────────────────────────────────────────────────────
st.title("🧪 BDD Test Case Generator")
st.markdown(
    "Enter a GitHub repository URL and branch name, then click **Generate** "
    "to produce Gherkin feature files from the source code."
)

if not openai_api_key:
    st.error("⚠️ OPENAI_API_KEY is not set. Add it to your `.env` file or environment variables.")
    st.stop()

col_url, col_branch = st.columns([3, 1])
with col_url:
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        help="Public or private repository URL (e.g. https://github.com/octocat/Hello-World).",
    )
with col_branch:
    branch = st.text_input(
        "Branch",
        value="main",
        help="Branch to analyse (e.g. main, master, develop).",
    )

generate_clicked = st.button(
    "🚀 Generate BDD Tests",
    type="primary",
    use_container_width=True,
    disabled=not repo_url,
)

# ── Generation logic ─────────────────────────────────────────────────────────
if generate_clicked:
    try:
        parse_github_url(repo_url)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    if not branch.strip():
        st.error("Branch name cannot be empty.")
        st.stop()

    # Clear previous results
    st.session_state.pop("feature_files", None)
    st.session_state.pop("files_found", None)

    with st.status("Working…", expanded=True) as status:
        st.write("📥 Fetching source files from GitHub…")
        try:
            source_files = fetch_repository_code(
                repo_url, branch.strip(), github_token or None
            )
        except ValueError as exc:
            status.update(label="Failed", state="error")
            st.error(str(exc))
            st.stop()
        except Exception as exc:
            status.update(label="Failed", state="error")
            st.error(f"Could not fetch repository: {exc}")
            st.stop()

        if not source_files:
            status.update(label="No source files found", state="error")
            st.error(
                "No supported source files were found in this repository/branch. "
                "Make sure the URL and branch are correct."
            )
            st.stop()

        st.write(f"✅ Found **{len(source_files)}** source file(s).")
        st.write("🤖 Generating BDD feature files with OpenAI…")

        try:
            feature_files = generate_bdd_tests(source_files, openai_api_key)
        except Exception as exc:
            status.update(label="Failed", state="error")
            st.error(f"BDD generation failed: {exc}")
            st.stop()

        status.update(
            label=f"Done — generated {len(feature_files)} feature file(s).",
            state="complete",
        )

    st.session_state["feature_files"] = feature_files
    st.session_state["files_found"] = len(source_files)

# ── Results ──────────────────────────────────────────────────────────────────
if st.session_state.get("feature_files"):
    feature_files: dict = st.session_state["feature_files"]

    st.divider()
    st.header("📋 Generated BDD Feature Files")
    st.caption(
        f"Analysed {st.session_state.get('files_found', '?')} source file(s) → "
        f"produced {len(feature_files)} feature file(s)."
    )

    # ── Download all as ZIP ──────────────────────────────────────────────────
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in feature_files.items():
            zf.writestr(f"features/{name}", content)
    zip_buffer.seek(0)

    st.download_button(
        label="📦 Download All Feature Files (.zip)",
        data=zip_buffer.getvalue(),
        file_name="bdd_features.zip",
        mime="application/zip",
        use_container_width=True,
    )

    st.divider()

    # ── Individual feature files ─────────────────────────────────────────────
    for feature_name, content in feature_files.items():
        with st.expander(f"📄 {feature_name}", expanded=True):
            st.code(content, language="gherkin")
            st.download_button(
                label=f"⬇️ Download {feature_name}",
                data=content,
                file_name=feature_name,
                mime="text/plain",
                key=f"dl_{feature_name}",
            )
