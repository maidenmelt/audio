from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ConversationRecord:
    """Одна запись разговора: метаданные + транскрипт."""

    def __init__(
        self,
        source_path: str = "",
        transcript: str = "",
        duration_sec: float = 0.0,
        language: str = "ru",
        recorded_at: Optional[Any] = None,
    ) -> None:
        # приватные поля инициализируются только через сеттеры
        # валидация в одном месте, а не размазана по коду
        self._source_path: str = ""
        self._transcript: str = ""
        self._duration_sec: float = 0.0
        self._language: str = "ru"
        self._recorded_at: Optional[datetime.date] = None

        self.source_path = source_path
        self.transcript = transcript
        self.duration_sec = duration_sec
        self.language = language
        self.recorded_at = recorded_at

    # конструктор копировани
    @classmethod
    def copy_from(cls, other: "ConversationRecord") -> "ConversationRecord":
        if not isinstance(other, ConversationRecord):
            raise TypeError("copy_from ожидает ConversationRecord")
        return cls(
            source_path=other._source_path,
            transcript=other._transcript,
            duration_sec=other._duration_sec,
            language=other._language,
            recorded_at=other._recorded_at,
        )

    #геттеры/сеттеры с валидацией
    @property
    def source_path(self) -> str:
        return self._source_path

    @source_path.setter
    def source_path(self, value: str) -> None:
        self._source_path = str(value or "").strip()

    @property
    def transcript(self) -> str:
        return self._transcript

    @transcript.setter
    def transcript(self, value: str) -> None:
        self._transcript = str(value or "")

    @property
    def duration_sec(self) -> float:
        return self._duration_sec

    @duration_sec.setter
    def duration_sec(self, value: Any) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Длительность должна быть числом, получено {value!r}")
        if number < 0:
            raise ValueError("Длительность не может быть отрицательной")
        self._duration_sec = number

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        text = str(value or "").strip().lower()
        if not text:
            raise ValueError("Язык не может быть пустым")
        self._language = text

    @property
    def recorded_at(self) -> Optional[datetime.date]:
        return self._recorded_at

    @recorded_at.setter
    def recorded_at(self, value: Any) -> None:
        if value is None or value == "":
            self._recorded_at = None
            return
        if isinstance(value, datetime.date):
            self._recorded_at = value
            return
        try:
            self._recorded_at = datetime.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Неверный формат даты: {value!r}")

    #производные (не меняют поля)
    @property
    def key(self) -> str:
        """Уникальный ключ записи имя файла без пути."""
        return Path(self._source_path).name if self._source_path else "unknown"

    @property
    def preview(self) -> str:
        text = self._transcript.strip()
        return text if len(text) <= 80 else text[:80] + "…"

    def is_empty(self) -> bool:
        return not self._transcript and self._duration_sec == 0.0

    #служебные методы
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConversationRecord):
            return NotImplemented
        return (
            self._source_path == other._source_path
            and self._transcript == other._transcript
            and self._duration_sec == other._duration_sec
            and self._language == other._language
            and self._recorded_at == other._recorded_at
        )

    def __hash__(self) -> int:
        return hash((self._source_path, self._duration_sec))

    def __repr__(self) -> str:
        return f"ConversationRecord(key={self.key!r}, duration={self._duration_sec:g}s)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self._source_path,
            "transcript": self._transcript,
            "duration_sec": self._duration_sec,
            "language": self._language,
            "recorded_at": self._recorded_at.isoformat() if self._recorded_at else "",
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationRecord":
        return cls(
            source_path=data.get("source_path", ""),
            transcript=data.get("transcript", ""),
            duration_sec=data.get("duration_sec", 0.0),
            language=data.get("language", "ru"),
            recorded_at=data.get("recorded_at") or None,
        )
