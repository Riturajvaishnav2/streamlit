# Client–Partner LLM Workflow

A Streamlit app that converts an uploaded file into Markdown, uses LLM prompts to
generate a common JSON, and walks through each client–partner pair to generate
TI/TO/IoT and loader outputs with human-in-the-loop edits.

## Prerequisites

- Python 3.9+
- OpenAI API key
- Docling (for converting uploads to Markdown/JSONL)
- Qdrant (optional, for prompt history storage)

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file (optional) to set defaults:

```bash
OPENAI_API_KEY=your-key
QDRANT_URL=https://your-qdrant-host
QDRANT_API_KEY=your-qdrant-key
QDRANT_COLLECTION=prompt_history
QDRANT_TOP_K=20
```

## Run

```bash
streamlit run src/streamlit_app.py
```

## Workflow

1. Upload a file and confirm the Markdown preview.
   - The app uses Docling to convert uploads to Markdown and JSONL.
2. Generate the common JSON with the selected prompt.
3. Edit client–partner pairs in the table and apply edits.
4. Step through each pair to generate TI/TO/IoT and loader output.
5. Save outputs or regenerate with chat notes.

## Convert any file to Markdown (CLI)

```bash
python scripts/convert_to_md.py path/to/input --output converted.md
```

## Qdrant prompt history

Set the following environment variables to enable history storage in Qdrant:

- `QDRANT_URL` (required)
- `QDRANT_API_KEY` (optional)
- `QDRANT_COLLECTION` (default: `prompt_history`)
- `QDRANT_TOP_K` (default: 20)

## Deploy (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, click "New app".
3. Select your repo, branch, and `streamlit_app.py` as the main file.
4. Click "Deploy".
