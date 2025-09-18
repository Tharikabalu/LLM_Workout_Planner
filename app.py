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


def get_current_user() -> str:
	"""Get current user identity - simplified for demo purposes"""
	# In a real app, this would come from authentication system
	# For now, we'll use a simple session state approach
	if 'current_user' not in st.session_state:
		st.session_state.current_user = None
	
	# User selection interface
	st.sidebar.subheader("👤 User Identity")
	user_options = ["Select User", "tharika", "Other User"]
	selected_user = st.sidebar.selectbox("Who are you?", user_options, key="user_selector")
	
	if selected_user != "Select User":
		st.session_state.current_user = selected_user
		st.sidebar.success(f"Logged in as: {selected_user}")
	
	return st.session_state.current_user


def get_api_keys() -> tuple[str | None, str | None]:
	# Sidebar API key inputs fall back to env vars
	st.sidebar.subheader("🤖 AI Provider Configuration")
	
	current_user = get_current_user()
	
	# Provider selection
	provider = st.sidebar.selectbox(
		"Choose AI Provider", 
		["openai", "google"], 
		index=0 if os.getenv("LLM_PROVIDER", "openai") == "openai" else 1
	)
	os.environ["LLM_PROVIDER"] = provider
	
	openai_key = None
	google_key = None
	
	# Check if user is tharika - they get automatic access to Google API key
	is_tharika = current_user == "tharika"
	
	if provider == "openai":
		st.sidebar.subheader("OpenAI API Key")
		openai_key_env = os.getenv("OPENAI_API_KEY")
		openai_key_input = st.sidebar.text_input("OPENAI_API_KEY", value=openai_key_env or "", type="password")
		if openai_key_input:
			os.environ["OPENAI_API_KEY"] = openai_key_input
			openai_key = openai_key_input
		else:
			openai_key = openai_key_env
	else:
		st.sidebar.subheader("Google API Key")
		
		if is_tharika:
			# Tharika gets automatic access to the Google API key
			google_key = "AIzaSyC5YeyH0pByYysF1bjG77vzeMua9rGJ3zc"
			os.environ["GOOGLE_API_KEY"] = google_key
			st.sidebar.success("🔑 Using Tharika's Google API key")
		else:
			# Other users need to provide their own API key
			st.sidebar.warning("⚠️ Please provide your own Google API key")
			google_key_env = os.getenv("GOOGLE_API_KEY")
			google_key_input = st.sidebar.text_input("GOOGLE_API_KEY", value=google_key_env or "", type="password")
			if google_key_input:
				os.environ["GOOGLE_API_KEY"] = google_key_input
				google_key = google_key_input
			else:
				google_key = google_key_env
	
	return openai_key, google_key


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
	
	# Get current user first
	current_user = get_current_user()
	
	# Show user-specific welcome message
	if current_user:
		if current_user == "tharika":
			st.success(f"Welcome back, {current_user}! You have access to the Google API key. 🎉")
		else:
			st.info(f"Welcome, {current_user}! Please provide your own API key to use the AI features.")
	else:
		st.info("👋 Please select your user identity in the sidebar to get started.")
	
	openai_key, google_key = get_api_keys()
	provider = os.getenv("LLM_PROVIDER", "openai")
	
	if current_user:
		if provider == "openai" and not openai_key:
			st.warning("Please provide OPENAI_API_KEY in the sidebar or your environment.")
		elif provider == "google" and not google_key:
			if current_user != "tharika":
				st.warning("Please provide your own GOOGLE_API_KEY in the sidebar.")
			else:
				st.error("There was an issue with the Google API key configuration.")
	else:
		st.warning("Please select your user identity in the sidebar to continue.")

	store = JsonWorkoutStore()
	with st.container():
		render_log_form(store)

	st.divider()
	logs = render_history(store)

	st.divider()
	
	# Only show planner if user has proper API access
	api_configured = False
	if current_user and provider == "openai" and openai_key:
		api_configured = True
	elif current_user and provider == "google" and google_key:
		api_configured = True
	
	if api_configured:
		render_planner(store)
	else:
		st.subheader("Generate next plan")
		if current_user:
			st.warning("⚠️ Please configure your API key to use the AI workout planner.")
		else:
			st.info("👋 Please select your user identity and configure your API key to use the AI workout planner.")


if __name__ == "__main__":
	main()
