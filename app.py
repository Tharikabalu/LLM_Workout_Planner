import os
import json
from datetime import date
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from storage import JsonWorkoutStore
from planner import generate_next_plan


load_dotenv(override=True)

st.set_page_config(page_title="Workout Planner (MVP)", page_icon="🏋️", layout="wide")


def get_api_key() -> str | None:
	# Sidebar API key input falls back to env var
	st.sidebar.subheader("API Key")
	api_key_env = os.getenv("OPENAI_API_KEY")
	api_key_input = st.sidebar.text_input("OPENAI_API_KEY", value=api_key_env or "", type="password")
	if api_key_input:
		os.environ["OPENAI_API_KEY"] = api_key_input
	return os.getenv("OPENAI_API_KEY")


def render_log_form(store: JsonWorkoutStore) -> None:
	st.subheader("Log today's workout")
	with st.form("log_form", clear_on_submit=True):
		col1, col2, col3 = st.columns(3)
		with col1:
			workout_date = st.date_input("Date", value=date.today())
		with col2:
			duration_min = st.number_input("Duration (min)", min_value=0, max_value=300, value=60)
		with col3:
			rpe = st.slider("Session RPE (1-10)", min_value=1, max_value=10, value=7)

		summary = st.text_area("Summary (movements, sets x reps, notes)")
		soreness = st.text_input("Soreness/Injuries (optional)")
		submit = st.form_submit_button("Save log")

		if submit:
			entry: Dict[str, Any] = {
				"date": workout_date.isoformat(),
				"duration_min": int(duration_min),
				"rpe": int(rpe),
				"summary": summary.strip(),
				"soreness": soreness.strip(),
			}
			store.add_log(entry)
			st.success("Log saved.")


def render_history(store: JsonWorkoutStore) -> List[Dict[str, Any]]:
	st.subheader("History")
	logs = store.get_logs()
	if not logs:
		st.info("No logs yet. Add your first workout above.")
		return []

	# Latest first for display
	df = pd.DataFrame(logs)
	df_display = df.iloc[::-1].reset_index(drop=True)
	st.dataframe(df_display, use_container_width=True)

	st.download_button(
		label="Export logs (JSON)",
		data=json.dumps({"logs": logs}, indent=2),
		file_name="workouts.json",
		mime="application/json",
	)
	return logs


def render_planner(store: JsonWorkoutStore) -> None:
	st.subheader("Generate next plan")
	goal = st.text_input("Goal (e.g., Hypertrophy, 5K PR, General Fitness)", value="General fitness")
	constraints = st.text_input("Constraints (equipment limits, time, injuries)")
	recent_limit = st.slider("Use last N logs", min_value=0, max_value=14, value=5)

	if st.button("Generate plan", type="primary"):
		with st.spinner("Thinking..."):
			recent_logs = store.get_recent(recent_limit) if recent_limit > 0 else []
			plan = generate_next_plan(recent_logs, goal=goal, constraints=constraints)
			st.markdown("### Suggested next session")
			st.markdown(plan)


def main() -> None:
	st.title("🏋️ Workout Planner")
	api_key = get_api_key()
	if not api_key:
		st.warning("Please provide OPENAI_API_KEY in the sidebar or your environment.")

	store = JsonWorkoutStore()
	with st.container():
		render_log_form(store)

	st.divider()
	logs = render_history(store)

	st.divider()
	render_planner(store)


if __name__ == "__main__":
	main()
