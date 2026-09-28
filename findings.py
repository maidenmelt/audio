from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class Finding(ABC):

    def __init__(self, present: bool = False) -> None:
        self._present: bool = bool(present)

    @property
    def present(self) -> bool:
        return self._present

    @present.setter
    def present(self, value: bool) -> None:
        self._present = bool(value)

    @abstractmethod
    def identify(self) -> str:
        raise NotImplementedError

    def describe(self) -> str:
        mark = "да" if self._present else "нет"
        return f"[{self.identify()}] обнаружено: {mark}"

    @classmethod
    def copy_from(cls, other: "Finding") -> "Finding":
        if not isinstance(other, Finding):
            raise TypeError("copy_from ожидает объект Finding")
        return type(other).from_dict(other.to_dict())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Finding):
            return NotImplemented
        return type(self) is type(other) and self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._present))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(present={self._present})"

    def to_dict(self) -> Dict[str, Any]:
        return {"cls": type(self).__name__, "present": self._present}


class RudenessFinding(Finding):

    def __init__(self, present: bool = False, who: str = "",
                 examples: Optional[List[str]] = None) -> None:
        super().__init__(present)
        self._who: str = str(who or "").strip()
        self._examples: List[str] = list(examples or [])

    @property
    def who(self) -> str:
        return self._who

    @who.setter
    def who(self, value: str) -> None:
        self._who = str(value or "").strip()

    @property
    def examples(self) -> List[str]:
        return list(self._examples)

    @examples.setter
    def examples(self, value: List[str]) -> None:
        self._examples = list(value or [])

    def identify(self) -> str:
        return "Грубость"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(who=self._who, examples=list(self._examples))
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RudenessFinding":
        return RudenessFinding(present=data.get("present", False),
                                who=data.get("who", ""),
                                examples=data.get("examples", []))


class SpecialOfferFinding(Finding):

    def __init__(self, present: bool = False, who: str = "",
                 details: str = "") -> None:
        super().__init__(present)
        self._who: str = str(who or "").strip()
        self._details: str = str(details or "").strip()

    @property
    def who(self) -> str:
        return self._who

    @who.setter
    def who(self, value: str) -> None:
        self._who = str(value or "").strip()

    @property
    def details(self) -> str:
        return self._details

    @details.setter
    def details(self, value: str) -> None:
        self._details = str(value or "").strip()

    def identify(self) -> str:
        return "Спецпредложение"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(who=self._who, details=self._details)
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SpecialOfferFinding":
        return SpecialOfferFinding(present=data.get("present", False),
                                    who=data.get("who", ""),
                                    details=data.get("details", ""))


class DissatisfactionFinding(Finding):

    def __init__(self, present: bool = False, reason: str = "",
                 examples: Optional[List[str]] = None) -> None:
        super().__init__(present)
        self._reason: str = str(reason or "").strip()
        self._examples: List[str] = list(examples or [])

    @property
    def reason(self) -> str:
        return self._reason

    @reason.setter
    def reason(self, value: str) -> None:
        self._reason = str(value or "").strip()

    @property
    def examples(self) -> List[str]:
        return list(self._examples)

    @examples.setter
    def examples(self, value: List[str]) -> None:
        self._examples = list(value or [])

    def identify(self) -> str:
        return "Недовольство"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(reason=self._reason, examples=list(self._examples))
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "DissatisfactionFinding":
        return DissatisfactionFinding(present=data.get("present", False),
                                       reason=data.get("reason", ""),
                                       examples=data.get("examples", []))


_FINDING_TYPES: Dict[str, Type[Finding]] = {
    "rudeness": RudenessFinding,
    "special_offer": SpecialOfferFinding,
    "dissatisfaction": DissatisfactionFinding,
}


def findings_from_analysis(analysis: Dict[str, Any]) -> List[Finding]:
    result: List[Finding] = []
    for key, cls in _FINDING_TYPES.items():
        block = analysis.get(key)
        if isinstance(block, dict):
            result.append(cls.from_dict(block))
    return result


def finding_class_by_name(name: str) -> Type[Finding]:
    for cls in _FINDING_TYPES.values():
        if cls.__name__ == name:
            return cls
    raise ValueError(f"Неизвестный класс находки: {name!r}")
