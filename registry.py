from __future__ import annotations

import json
from typing import (Any, Callable, Generic, Iterator, List, Optional, Tuple,
                     TypeVar)

K = TypeVar("K")
V = TypeVar("V")


class FindingRegistry(Generic[K, V]):

    def __init__(self, bucket_count: int = 16) -> None:
        if bucket_count < 1:
            raise ValueError("Число корзин должно быть >= 1")
        self._bucket_count: int = bucket_count
        self._buckets: List[List[List[Any]]] = [[] for _ in range(bucket_count)]
        self._size: int = 0

    # конструктор копирования / деструктор
    @classmethod
    def copy_from(cls, other: "FindingRegistry[K, V]") -> "FindingRegistry[K, V]":
        clone: "FindingRegistry[K, V]" = cls(bucket_count=other._bucket_count)
        for key, value in other.items():
            clone.insert(key, value)
        return clone

    def __del__(self) -> None:
        try:
            self.clear()
        except Exception:
            pass

    # внутреннее
    def _index(self, key: K) -> int:
        return hash(key) % self._bucket_count

    # основные операции
    def insert(self, key: K, value: V) -> None:
        bucket = self._buckets[self._index(key)]
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value
                return
        bucket.append([key, value])
        self._size += 1

    def __lshift__(self, item: Tuple[K, V]) -> "FindingRegistry[K, V]":
        try:
            key, value = item
        except (TypeError, ValueError):
            raise TypeError("Оператор << ожидает пару (ключ, значение)")
        self.insert(key, value)
        return self

    def __getitem__(self, key: K) -> V:
        bucket = self._buckets[self._index(key)]
        for k, v in bucket:
            if k == key:
                return v
        raise KeyError(key)

    def __setitem__(self, key: K, value: V) -> None:
        self.insert(key, value)

    def contains(self, key: K) -> bool:
        bucket = self._buckets[self._index(key)]
        return any(k == key for k, _ in bucket)

    def __contains__(self, key: K) -> bool:
        return self.contains(key)

    def count(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    def remove(self, key: K) -> bool:
        bucket = self._buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def clear(self) -> None:
        self._buckets = [[] for _ in range(self._bucket_count)]
        self._size = 0

    #обход
    def keys(self) -> Iterator[K]:
        for bucket in self._buckets:
            for k, _ in bucket:
                yield k

    def values(self) -> Iterator[V]:
        for bucket in self._buckets:
            for _, v in bucket:
                yield v

    def items(self) -> Iterator[Tuple[K, V]]:
        for bucket in self._buckets:
            for k, v in bucket:
                yield (k, v)

    def __iter__(self) -> Iterator[K]:
        return self.keys()

    #сравнение и пересечение
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FindingRegistry):
            return NotImplemented
        if len(self) != len(other):
            return False
        return all(other.contains(k) and other[k] == v for k, v in self.items())

    def __and__(self, other: "FindingRegistry[K, V]") -> "FindingRegistry[K, V]":
        """Пересечение: все пары (ключ, значение), общие для обеих коллекций."""
        result: "FindingRegistry[K, V]" = FindingRegistry(bucket_count=self._bucket_count)
        for k, v in self.items():
            if other.contains(k) and other[k] == v:
                result.insert(k, v)
        return result

    def __repr__(self) -> str:
        return f"FindingRegistry(size={self._size}, buckets={self._bucket_count})"

    #доменный доступ (не только CRUD)
    def find_by_type(self, finding_type: str) -> List[V]:
        """Все значения, чей identify() совпадает с finding_type
        (например 'Грубость') — удобно для отчётов и для GUI."""
        return [v for v in self.values()
                if hasattr(v, "identify") and v.identify() == finding_type]

    #сохранение / загрузка
    def save(self, path: str, value_to_dict: Optional[Callable[[V], Any]] = None) -> None:
        convert = value_to_dict or (lambda v: v.to_dict() if hasattr(v, "to_dict") else v)
        data = [{"key": k, "value": convert(v)} for k, v in self.items()]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str,
             value_from_dict: Optional[Callable[[Any], V]] = None) -> "FindingRegistry[Any, Any]":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        registry: "FindingRegistry[Any, Any]" = cls()
        for row in data:
            value = row["value"]
            if value_from_dict is not None:
                value = value_from_dict(value)
            registry.insert(row["key"], value)
        return registry
