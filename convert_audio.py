from moviepy import VideoFileClip


def convert_mp4_to_wav(input_file: str, output_file: str) -> None:
    """Извлекает аудиодорожку из видео в WAV 16 kHz mono"""
    print(f"Открываю {input_file}")
    clip = VideoFileClip(input_file)

    print(f"Длительность: {clip.duration} сек")
    print(f"Сохраняю аудио в {output_file}")

    clip.audio.write_audiofile(
        output_file,
        fps=16000,
        nbytes=2,
        codec="pcm_s16le",
        ffmpeg_params=["-ac", "1"]  # моно
    )

    clip.close()
    print("Готово")


if __name__ == "__main__":
    convert_mp4_to_wav(
        input_file="data/audio/conversation.mp4",
        output_file="data/audio/conversation.wav"
    )