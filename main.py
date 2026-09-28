import argparse
import json
import logging
import os
from datetime import datetime

from config import settings
from transcriber import Transcriber
from analyzer import Analyzer
from models import ConversationRecord
from findings import findings_from_analysis
from archive import ConversationArchive
from registry import FindingRegistry
from gui import add_to_session, run_console, run_gui
import tests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    audio_path = settings.AUDIO_DIR / settings.AUDIO_FILE

    if not audio_path.exists():
        print(f"Аудиофайл не найден: {audio_path}")
        return

    print("=" * 60)
    print("ТРАНСКРИПЦИЯ АУДИО")
    print("=" * 60)
    transcriber = Transcriber()
    text, duration_sec = transcriber.transcribe(str(audio_path))

    print("\nТекст разговора:")
    print("-" * 60)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 60)

    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    transcript_file = settings.RESULTS_DIR / f"transcript_{timestamp}.txt"
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"\nТранскрипт сохранён: {transcript_file}")

    print("\n" + "=" * 60)
    print("АНАЛИЗ ЧЕРЕЗ LLM")
    print("=" * 60)
    analyzer = Analyzer()
    result = analyzer.analyze(text)

    result_file = settings.RESULTS_DIR / f"analysis_{timestamp}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\nРезультат анализа:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nСохранено: {result_file}")

    record = ConversationRecord(source_path=str(audio_path), transcript=text,
                                 duration_sec=duration_sec)
    findings = findings_from_analysis(result)

    archive = ConversationArchive()
    registry: "FindingRegistry" = FindingRegistry()
    add_to_session(archive, registry, record, findings)

    registry_file = settings.RESULTS_DIR / f"registry_{timestamp}.json"
    registry.save(str(registry_file))
    print(f"Реестр находок сохранён: {registry_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audio Analyzer")
    parser.add_argument("--gui", action="store_true", help="открыть графический интерфейс")
    parser.add_argument("--menu", action="store_true", help="открыть консольное меню")
    parser.add_argument("--test", action="store_true", help="запустить самопроверки (assert)")
    args = parser.parse_args()

    if args.test:
        tests.run_all()
        return

    if args.menu:
        run_console(ConversationArchive(), FindingRegistry())
        return

    if args.gui:
        run_gui(ConversationArchive(), FindingRegistry())
        return

    run_pipeline()


if __name__ == "__main__":
    main()
