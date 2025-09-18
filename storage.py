import json
import os
from datetime import datetime
from typing import Any, Dict, List


class JsonWorkoutStore:
	"""Local JSON storage for workout logs.

	Creates the file on first use and keeps an in-memory cache for quick reads.
	"""

	def __init__(self, file_path: str = "data/workouts.json") -> None:
		self.file_path = file_path
		self._ensure_file()

	def _ensure_file(self) -> None:
		os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
		if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
			with open(self.file_path, "w", encoding="utf-8") as f:
				json.dump({"logs": []}, f)

	def get_logs(self) -> List[Dict[str, Any]]:
		with open(self.file_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return data.get("logs", [])

	def add_log(self, log: Dict[str, Any]) -> None:
		logs = self.get_logs()
		log = {"created_at": datetime.utcnow().isoformat() + "Z", **log}
		logs.append(log)
		with open(self.file_path, "w", encoding="utf-8") as f:
			json.dump({"logs": logs}, f, indent=2)

	def get_recent(self, limit: int = 7) -> List[Dict[str, Any]]:
		logs = self.get_logs()
		return logs[-limit:]

	def export_json(self) -> str:
		with open(self.file_path, "r", encoding="utf-8") as f:
			return f.read()
