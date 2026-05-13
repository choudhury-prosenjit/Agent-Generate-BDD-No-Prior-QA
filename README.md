# Agent-Generate-BDD-No-Prior-QA

AI-powered **Streamlit web app** that analyses any GitHub repository and generates BDD test scenarios in Gherkin Given-When-Then format using the OpenAI API — no prior QA artefacts required.

## Features

- 🌐 **Streamlit UI** — paste a GitHub URL, enter your API key, click Generate.
- 🔍 Fetches source files directly via the **GitHub API** (no local git clone needed).
- 🧠 Uses **GPT-4o-mini** to produce feature files per module.
- 📦 Download all feature files as a single **ZIP archive**.
- 🔒 API keys are used only for the current session and never stored.

## Project Structure

```
app.py                  # Streamlit entry-point
src/
  github_fetcher.py     # GitHub API fetcher & file filter
  bdd_generator.py      # OpenAI BDD generation logic
requirements.txt        # Python dependencies
.env                    # Local secrets (not committed)
```

## Setup

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API key
Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-...
```
> Or enter it directly in the app sidebar at runtime.

## Run

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**.

## Usage

1. Paste a GitHub repository URL (e.g. `https://github.com/owner/repo`).
2. Set the branch name (default: `main`).
3. Enter your **OpenAI API Key** in the sidebar.
4. *(Optional)* Enter a **GitHub Token** for higher rate limits or private repos.
5. Click **🚀 Generate BDD Tests**.
6. Browse generated feature files and download them individually or as a ZIP.

## Notes

- Skips `node_modules`, `.git`, `vendor`, `dist`, `build`, test folders, etc.
- Supports: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.go`, `.rb`, `.cs`, `.cpp`, `.php`, `.swift`, `.kt`, `.rs`
- Max 30 files fetched, 50 KB per file, 150 KB total context per run.
