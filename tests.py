from __future__ import annotations

import os
import tempfile
import time

from archive import ConversationArchive, measure_memory_usage
from findings import (DissatisfactionFinding, Finding, RudenessFinding,
                       SpecialOfferFinding, finding_class_by_name,
                       findings_from_analysis)
from models import ConversationRecord
from registry import FindingRegistry


def test_lab1_models() -> None:
    """конструкторы, инкапсуляция, валидация."""
    empty = ConversationRecord()
    assert empty.is_empty()
    assert empty.duration_sec == 0.0
    assert empty.language == "ru"
    assert empty.recorded_at is None

    rec = ConversationRecord(source_path="data/audio/conversation.wav",
                              transcript="Здравствуйте, чем могу помочь?",
                              duration_sec=125.5, language="RU",
                              recorded_at="2026-09-10")
    assert not rec.is_empty()
    assert rec.key == "conversation.wav"
    assert rec.language == "ru"  # приведение к нижнему регистру
    assert rec.recorded_at.isoformat() == "2026-09-10"
    assert len(rec.preview) <= 81

    copy = ConversationRecord.copy_from(rec)
    assert copy == rec and copy is not rec
    copy.transcript = "другой текст"
    assert rec.transcript != copy.transcript  # копия независима

    for bad_duration in (-1, "не число"):
        try:
            rec.duration_sec = bad_duration
            assert False, "ожидалась ValueError на некорректную длительность"
        except ValueError:
            pass

    try:
        rec.language = ""
        assert False, "пустой язык должен вызывать ValueError"
    except ValueError:
        pass

    try:
        rec.recorded_at = "неверная-дата"
        assert False, "некорректная дата должна вызывать ValueError"
    except ValueError:
        pass

    data = rec.to_dict()
    restored = ConversationRecord.from_dict(data)
    assert restored == rec

    # эффективность: обработка 1000 записей укладывается в 0.5
    start = time.perf_counter()
    for _ in range(1000):
        ConversationRecord(source_path="x.wav", transcript="текст", duration_sec=10)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"обработка 1000 записей заняла {elapsed:.3f}с"

    print("ConversationRecord — OK")


def test_lab2_findings() -> None:
    """виртуальный identify(), наследники."""
    try:
        Finding(present=True)  # type: ignore[abstract]
        assert False, "Finding не должен создаваться напрямую (абстрактный класс)"
    except TypeError:
        pass

    rude = RudenessFinding(present=True, who="оператор", examples=["повысил голос"])
    offer = SpecialOfferFinding(present=False)
    dissatisfaction = DissatisfactionFinding(present=True, reason="долгое ожидание",
                                              examples=["клиент попросил жалобную книгу"])

    assert isinstance(rude, Finding) and isinstance(offer, Finding)
    ids = {rude.identify(), offer.identify(), dissatisfaction.identify()}
    assert len(ids) == 3, "identify() должен различаться у каждого наследника"
    assert rude.describe().startswith(f"[{rude.identify()}]")

    offer.present = True
    offer.who = "менеджер"
    offer.details = "скидка 15% при продлении"
    assert offer.present and offer.who == "менеджер" and offer.details

    rude_copy = Finding.copy_from(rude)
    assert rude_copy == rude and rude_copy is not rude
    updated = rude_copy.examples
    updated.append("не должно попасть в оригинал")
    rude_copy.examples = updated
    assert len(rude.examples) == 1        # оригинал не задет
    assert len(rude_copy.examples) == 2   # а копия обновилась

    analysis = {
        "rudeness": {"present": True, "who": "оператор", "examples": ["перебил клиента"]},
        "special_offer": {"present": False},
        "dissatisfaction": {"present": True, "reason": "не решили вопрос", "examples": []},
    }
    findings = findings_from_analysis(analysis)
    assert len(findings) == 3
    assert any(f.identify() == "Грубость" and f.present for f in findings)
    assert finding_class_by_name("SpecialOfferFinding") is SpecialOfferFinding

    dissatisfaction_copy = DissatisfactionFinding.from_dict(dissatisfaction.to_dict())
    assert dissatisfaction_copy == dissatisfaction

    print("Finding и наследники — OK")


def test_lab3_archive() -> None:
    """ConversationArchive: контейнер STL (dict), обоснованное обращение."""
    archive = ConversationArchive()
    assert len(archive) == 0
    assert repr(archive) == "ConversationArchive(size=0)"

    r1 = ConversationRecord(source_path="a.wav", duration_sec=30)
    r2 = ConversationRecord(source_path="b.wav", duration_sec=200)
    archive.add(r1)
    archive.add(r2)
    assert len(archive) == 2
    assert "a.wav" in archive
    assert archive.get("a.wav") is r1
    assert set(archive.keys()) == {"a.wav", "b.wav"}
    assert r2 in list(archive.values())
    assert archive.with_duration_over(100) == [r2]

    cloned = ConversationArchive.copy_from(archive)
    assert len(cloned) == 2
    assert cloned.get("a.wav") == r1
    assert cloned.get("a.wav") is not r1  # независимая копия

    assert archive.remove("a.wav") and len(archive) == 1
    assert not archive.remove("a.wav")  # уже удалён — второй раз не найдёт

    def build() -> ConversationArchive:
        big = ConversationArchive()
        for i in range(500):
            big.add(ConversationRecord(source_path=f"file_{i}.wav",
                                        transcript="текст " * 20, duration_sec=i))
        return big

    peak_bytes = measure_memory_usage(build)
    assert peak_bytes > 0
    print(f"ConversationArchive — OK (пик памяти на 500 записей: {peak_bytes / 1024:.1f} КБ)")


def test_lab4_registry() -> None:
    """FindingRegistry: собственная хеш-таблица, операторы, save/load."""
    reg: "FindingRegistry[str, Finding]" = FindingRegistry(bucket_count=4)
    assert len(reg) == 0 and reg.count() == 0

    f1 = RudenessFinding(present=True, who="клиент")
    f2 = SpecialOfferFinding(present=True, who="менеджер", details="скидка 10%")
    reg << ("c1::Rudeness", f1) << ("c2::Offer", f2)
    assert len(reg) == 2
    assert "c1::Rudeness" in reg and reg["c1::Rudeness"] is f1

    reg["c3::Extra"] = DissatisfactionFinding(present=True, reason="долгое ожидание")
    assert reg["c3::Extra"].reason == "долгое ожидание"
    assert set(iter(reg)) == set(reg.keys())

    assert reg.remove("c2::Offer") and len(reg) == 2
    assert not reg.remove("такого нет")

    found = reg.find_by_type("Грубость")
    assert len(found) == 1 and found[0] is f1

    try:
        reg << "не пара"
        assert False, "оператор << должен требовать пару (ключ, значение)"
    except TypeError:
        pass

    try:
        FindingRegistry(bucket_count=0)
        assert False, "0 корзин должно быть ошибкой"
    except ValueError:
        pass

    a: "FindingRegistry[str, str]" = FindingRegistry()
    b: "FindingRegistry[str, str]" = FindingRegistry()
    for k in ("x", "y", "z"):
        a.insert(k, "v" + k)
    for k in ("y", "z", "w"):
        b.insert(k, "v" + k)
    common = a & b
    assert set(common.keys()) == {"y", "z"}
    assert FindingRegistry.copy_from(a) == a

    path = os.path.join(tempfile.mkdtemp(), "reg.json")
    reg.save(path)
    loaded = FindingRegistry.load(
        path, value_from_dict=lambda d: finding_class_by_name(d["cls"]).from_dict(d))
    assert len(loaded) == len(reg)
    assert loaded["c1::Rudeness"] == f1

    reg.clear()
    assert len(reg) == 0

    print("indingRegistry — OK")


def run_all() -> None:
    test_lab1_models()
    test_lab2_findings()
    test_lab3_archive()
    test_lab4_registry()
    print("\nВсе самопроверки пройдены.")


if __name__ == "__main__":
    run_all()
