import os
import subprocess


def to_wav(path: str, id: str) -> str:
    """
    Convert .ogg/OPUS to .wav
    """
    os.makedirs("downloads", exist_ok=True)
    wav_path = f"downloads/{id}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", path, wav_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    if os.path.exists(path):
        os.remove(path)
    return wav_path
