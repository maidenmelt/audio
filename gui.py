from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from archive import ConversationArchive
from findings import Finding, finding_class_by_name, findings_from_analysis
from models import ConversationRecord
from registry import FindingRegistry


def load_result_pair(analysis_path: str, transcript_path: str = "") -> Tuple[ConversationRecord, List[Finding]]:
    """(main.py -> transcriber.py + analyzer.py)."""
    with open(analysis_path, "r", encoding="utf-8") as fh:
        analysis = json.load(fh)

    transcript = ""
    if transcript_path and Path(transcript_path).exists():
        with open(transcript_path, "r", encoding="utf-8") as fh:
            transcript = fh.read()

    record = ConversationRecord(source_path=analysis_path, transcript=transcript)
    findings = findings_from_analysis(analysis)
    return record, findings


def add_to_session(archive: "ConversationArchive", registry: "FindingRegistry[str, Finding]",
                    record: ConversationRecord, findings: List[Finding]) -> None:
    archive.add(record)
    for finding in findings:
        registry.insert(f"{record.key}::{type(finding).__name__}", finding)


def _finding_from_raw(data: dict) -> Finding:
    cls = finding_class_by_name(data.get("cls", ""))
    return cls.from_dict(data)


# консольный интерфейс

def run_console(archive: ConversationArchive, registry: "FindingRegistry[str, Finding]") -> None:
    menu = ("\n1) список разговоров   2) находки по разговору\n"
            "3) добавить из results/   4) сохранить реестр   5) загрузить реестр\n"
            "0) выход\n> ")
    while True:
        choice = input(menu).strip()
        if choice == "0":
            break
        elif choice == "1":
            if not len(archive):
                print("   архив пуст")
            for key in archive.keys():
                print("   ", archive.get(key))
        elif choice == "2":
            key = input("   имя файла записи: ").strip()
            matches = [f for k, f in registry.items() if k.startswith(key + "::")]
            if not matches:
                print("   находок нет")
            for f in matches:
                print("   ", f.describe())
        elif choice == "3":
            analysis_path = input("   путь к analysis_*.json: ").strip()
            transcript_path = input("   путь к transcript_*.txt (можно пусто): ").strip()
            try:
                record, findings = load_result_pair(analysis_path, transcript_path)
                add_to_session(archive, registry, record, findings)
                print(f"   добавлено: {record.key}, находок: {len(findings)}")
            except Exception as err:
                print("   ошибка:", err)
        elif choice == "4":
            path = input("   сохранить реестр как: ").strip() or "results/registry.json"
            registry.save(path)
            print("   сохранено:", path)
        elif choice == "5":
            path = input("   загрузить реестр из: ").strip() or "results/registry.json"
            loaded = FindingRegistry.load(path, value_from_dict=_finding_from_raw)
            registry.clear()
            for k, v in loaded.items():
                registry.insert(k, v)
            print("   загружено находок:", len(registry))
        else:
            print("   неизвестный пункт меню")


# графический интерфейс

def run_gui(archive: ConversationArchive, registry: "FindingRegistry[str, Finding]") -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Audio Analyzer — разговоры и находки")
    root.geometry("880x600")

    status_var = tk.StringVar(value=f"Записей: {len(archive)}")

    top = tk.Frame(root)
    top.pack(fill="x", padx=10, pady=8)

    def refresh() -> None:
        tree.delete(*tree.get_children())
        for key, finding in registry.items():
            record_key = key.split("::", 1)[0]
            tree.insert("", "end", values=(
                record_key, finding.identify(),
                "да" if finding.present else "нет", finding.describe()))
        status_var.set(f"Записей: {len(archive)}, находок: {len(registry)}")

    def browse_and_add() -> None:
        analysis_path = filedialog.askopenfilename(
            title="Файл анализа (analysis_*.json)", filetypes=[("JSON", "*.json")])
        if not analysis_path:
            return
        transcript_path = filedialog.askopenfilename(
            title="Файл транскрипта (можно отменить)", filetypes=[("Текст", "*.txt")])
        try:
            record, findings = load_result_pair(analysis_path, transcript_path or "")
            add_to_session(archive, registry, record, findings)
            refresh()
        except Exception as err:
            messagebox.showerror("Ошибка", str(err))

    def on_save() -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="registry.json")
        if not path:
            return
        registry.save(path)
        messagebox.showinfo("Сохранено", f"Находок сохранено: {len(registry)}")

    def on_load() -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            loaded = FindingRegistry.load(path, value_from_dict=_finding_from_raw)
        except Exception as err:
            messagebox.showerror("Ошибка", str(err))
            return
        registry.clear()
        for k, v in loaded.items():
            registry.insert(k, v)
        refresh()

    ttk.Button(top, text="Добавить результат…", command=browse_and_add).pack(side="left", padx=4)
    ttk.Button(top, text="Сохранить реестр", command=on_save).pack(side="left", padx=4)
    ttk.Button(top, text="Загрузить реестр", command=on_load).pack(side="left", padx=4)

    cols = ("record", "type", "present", "detail")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=18)
    headers = {"record": "Разговор", "type": "Тип находки", "present": "Есть?", "detail": "Детали"}
    for c in cols:
        tree.heading(c, text=headers[c])
    tree.column("record", width=180)
    tree.column("type", width=140)
    tree.column("present", width=60, anchor="center")
    tree.column("detail", width=380)
    tree.pack(fill="both", expand=True, padx=10, pady=6)

    tk.Label(root, textvariable=status_var, anchor="w").pack(fill="x", padx=10, pady=(0, 8))

    refresh()
    root.mainloop()
