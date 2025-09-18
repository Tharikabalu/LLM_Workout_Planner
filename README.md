## LLM-powered Workout Planner (MVP)

This MVP lets you log daily workouts and generate a tailored next-session plan using LangChain.

### Setup

1) Create and activate a virtual environment (optional)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Configure your API key
- Set `OPENAI_API_KEY` in your environment or create a `.env` file:
```bash
cp .env.example .env
# edit .env and add your key
```

### Run
```bash
streamlit run app.py
```

### Notes
- Logs are stored locally at `data/workouts.json`.
- The plan uses your recent history + goal to propose a balanced next session.
- You can export your logs from the UI.
