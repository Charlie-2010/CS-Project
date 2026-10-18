"""Application configuration loaded from the process environment."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


@dataclass(frozen=True)
class DatabaseConfig:
	host: str = "localhost"
	port: int = 3306
	user: str = "root"
	password: str = ""
	database: str = "scholarsync_db"

	@classmethod
	def from_env(cls) -> "DatabaseConfig":
		return cls(
			host=os.getenv("DB_HOST", "localhost"),
			port=int(os.getenv("DB_PORT", "3306")),
			user=os.getenv("DB_USER", "root"),
			password=os.getenv("DB_PASSWORD", ""),
			database=os.getenv("DB_NAME", "scholarsync_db"),
		)
