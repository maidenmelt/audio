import logging
from typing import Tuple

from faster_whisper import WhisperModel
from config import settings

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self):
        logger.info(f"Загрузка модели Whisper: {settings.WHISPER_MODEL}")
        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type="int8"
        )

    def transcribe(self, audio_path: str) -> Tuple[str, float]:
        """Возвращает (текст, длительность_в_секундах).

        Длительность теперь возвращается явно
        """
        logger.info(f"Транскрипция: {audio_path}")

        segments, info = self.model.transcribe(
            audio_path,
            language=settings.WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=True
        )

        logger.info(f"Длительность аудио: {info.duration} сек")

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts)
        logger.info(f"Получено символов: {len(full_text)}")

        return full_text, float(info.duration)
