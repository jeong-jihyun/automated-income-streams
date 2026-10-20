"""음성 제공자. 교체 가능한 구조: silent(시험용 무음), folder(직접 녹음 파일), edge-tts(선택 설치)."""
import os
import shutil
import subprocess
import wave


def write_silence(path, seconds, rate):
    n = int(seconds * rate)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)


def to_wav(src, dst, rate):
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg 가 설치되어 있지 않습니다.")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", str(rate), "-sample_fmt", "s16", dst],
                   check=True)


class SilentProvider:
    """시험용 가짜 음성: 글자 수에 비례한 무음. 실제 판매용이 아닙니다."""
    name = "silent"

    def __init__(self, cfg, **_):
        self.rate = cfg["sample_rate"]

    def synth(self, row, out_wav):
        write_silence(out_wav, max(0.5, 0.06 * len(row["text"])), self.rate)


class FolderProvider:
    """직접 녹음한 파일 사용: 폴더에 <번호>.wav / .mp3 / .m4a"""
    name = "folder"

    def __init__(self, cfg, folder=None, **_):
        if not folder or not os.path.isdir(folder):
            raise FileNotFoundError(f"녹음 파일 폴더가 없습니다: {folder}")
        self.folder, self.rate = folder, cfg["sample_rate"]

    def synth(self, row, out_wav):
        for ext in (".wav", ".mp3", ".m4a"):
            p = os.path.join(self.folder, row["no"] + ext)
            if os.path.isfile(p):
                to_wav(p, out_wav, self.rate)
                return
        raise FileNotFoundError(f"{row['no']}번 문장의 녹음 파일이 없습니다 ({self.folder})")


class EdgeTtsProvider:
    """edge-tts 는 비공식 도구라 상업 이용 약관 위험이 있습니다. 판매용이면 약관이 명확한 음성으로 바꾸세요."""
    name = "edge-tts"

    def __init__(self, cfg, **_):
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            raise RuntimeError("edge-tts 가 설치되어 있지 않습니다 (pip install edge-tts). 약관·상업 이용 조건을 먼저 확인하세요.")
        self.cfg = cfg

    def synth(self, row, out_wav):
        import asyncio, tempfile
        import edge_tts
        mp3 = tempfile.mktemp(suffix=".mp3")
        asyncio.run(edge_tts.Communicate(row["text"], self.cfg["voice"]).save(mp3))
        to_wav(mp3, out_wav, self.cfg["sample_rate"])
        os.remove(mp3)


PROVIDERS = {"silent": SilentProvider, "folder": FolderProvider, "edge-tts": EdgeTtsProvider}


def get_provider(name, cfg, **kw):
    if name not in PROVIDERS:
        raise ValueError(f"알 수 없는 음성 제공자 '{name}'. 선택: {', '.join(PROVIDERS)}")
    return PROVIDERS[name](cfg, **kw)
