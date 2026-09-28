from __future__ import annotations

import tracemalloc
from typing import Callable, Dict, Iterator, List, Optional

from models import ConversationRecord


class ConversationArchive:
    """Хранилище записей разговоров поверх dict[str, ConversationRecord]."""

    def __init__(self) -> None:
        self._records: Dict[str, ConversationRecord] = {}

    @classmethod
    def copy_from(cls, other: "ConversationArchive") -> "ConversationArchive":
        clone = cls()
        for record in other.values():
            clone.add(ConversationRecord.copy_from(record))
        return clone

    def add(self, record: ConversationRecord) -> None:
        if not isinstance(record, ConversationRecord):
            raise TypeError("В архив можно добавлять только ConversationRecord")
        self._records[record.key] = record

    def remove(self, key: str) -> bool:
        return self._records.pop(key, None) is not None

    def get(self, key: str) -> Optional[ConversationRecord]:
        return self._records.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._records

    def __len__(self) -> int:
        return len(self._records)

    def keys(self) -> Iterator[str]:
        return iter(self._records.keys())

    def values(self) -> Iterator[ConversationRecord]:
        return iter(self._records.values())

    def with_duration_over(self, seconds: float) -> List[ConversationRecord]:
        """Пример обращения к внутреннему хранилищу: записи длиннее порога."""
        return [r for r in self._records.values() if r.duration_sec > seconds]

    def __repr__(self) -> str:
        return f"ConversationArchive(size={len(self._records)})"


def measure_memory_usage(build_archive: Callable[[], ConversationArchive]) -> int:
    """Замер пиковой памяти при построении архива — Python-аналог psapi.h
    из методички (там же явно разрешён 'psapi.h или аналог').

    build_archive: функция без аргументов, строящая и возвращающая архив.
    Возвращает пиковое использование памяти в байтах.
    """
    tracemalloc.start()
    try:
        build_archive()
        _current, peak = tracemalloc.get_traced_memory()
        return peak
    finally:
        tracemalloc.stop()
