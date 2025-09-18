import os
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


def _get_openai_model_name() -> str:
	return os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")


def _get_google_model_name() -> str:
	return os.getenv("GOOGLE_MODEL_NAME", "gemini-pro")


def _get_temperature() -> float:
	try:
		return float(os.getenv("MODEL_TEMPERATURE", "0.4"))
	except ValueError:
		return 0.4


def _get_llm_provider() -> str:
	return os.getenv("LLM_PROVIDER", "openai").lower()


def generate_next_plan(recent_logs: List[Dict[str, Any]], goal: str, constraints: str | None = None) -> str:
	"""Generate a next-session workout plan using recent logs and a user goal."""
	provider = _get_llm_provider()
	
	if provider == "google":
		model = ChatGoogleGenerativeAI(
			model=_get_google_model_name(),
			temperature=_get_temperature(),
			google_api_key=os.getenv("GOOGLE_API_KEY")
		)
	else:
		model = ChatOpenAI(model=_get_openai_model_name(), temperature=_get_temperature())

	prompt = ChatPromptTemplate.from_messages([
		("system", (
			"You are an expert strength and conditioning coach. "
			"Design safe, progressive workout sessions. Favor balance across movement patterns, "
			"avoid overworking sore muscle groups, and adapt to user goals and constraints. "
			"Return the plan in a concise, structured bullet list with clear sets x reps, rest, and cues."
		)),
		("user", (
			"User goal: {goal}\n"
			"Constraints: {constraints}\n"
			"Recent logs (most recent last):\n{recent}\n\n"
			"Now propose the next session. Include warm-up, main lifts, accessories, and cooldown."
		)),
	])

	recent_text = "\n".join([
		f"- {log.get('date', log.get('created_at', ''))}: {log.get('summary', '')} "
		f"(RPE {log.get('rpe', 'n/a')}, duration {log.get('duration_min', 'n/a')} min)"
		for log in recent_logs
	]) or "(no history)"

	chain = prompt | model
	response = chain.invoke({
		"goal": goal or "general fitness",
		"constraints": constraints or "none",
		"recent": recent_text,
	})
	return response.content.strip()
