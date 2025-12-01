from __future__ import annotations
import sys
from pathlib import Path
import subprocess

from config import RAW_DIR, PROCESSED_DIR, DEFAULT_OUTPUT_JSON

ROLES_CSV = RAW_DIR / "roles.csv"


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def ensure_roles_csv():
    if not ROLES_CSV.exists():
        ROLES_CSV.write_text("speaker,role\nUNK,Unknown\n", encoding="utf-8")


def cleanup_previous_run():
    """
    Delete old transcript .txt files and old actions.json
    so that each video run produces a fresh, clean output.
    """
    # Delete all old transcripts
    for txt in RAW_DIR.glob("*.txt"):
        try:
            txt.unlink()
            print(f"[cleanup] Deleted old transcript: {txt}")
        except Exception as e:
            print(f"[cleanup] Could not delete {txt}: {e}")

    # Delete old actions.json
    if DEFAULT_OUTPUT_JSON.exists():
        try:
            DEFAULT_OUTPUT_JSON.unlink()
            print(f"[cleanup] Deleted old actions: {DEFAULT_OUTPUT_JSON}")
        except Exception as e:
            print(f"[cleanup] Could not delete {DEFAULT_OUTPUT_JSON}: {e}")


def transcribe_with_whisper(video_path: Path, out_txt: Path):
    try:
        import whisper
    except Exception:
        print("ERROR: Whisper not installed. Run: pip install openai-whisper ffmpeg-python")
        sys.exit(1)

    print(f"[video] Loading Whisper model (small)…")
    model = whisper.load_model("small")

    print(f"[video] Transcribing: {video_path}")
    # fp16=False for CPU on Windows
    result = model.transcribe(str(video_path), language="en", fp16=False)
    segments = result.get("segments", [])

    with out_txt.open("w", encoding="utf-8") as f:
        for seg in segments:
            text = seg.get("text", "").strip()
            if text:
                # No speaker diarization → mark as UNK
                f.write(f"UNK: {text}\n")

    print(f"[video] Wrote transcript -> {out_txt}")


def run_python(path: str):
    """Run an existing script like train_ml.py / infer_ml.py."""
    cmd = [sys.executable, path]
    print(f"[run] {' '.join(cmd)}")
    p = subprocess.run(cmd, shell=False)
    if p.returncode != 0:
        print(f"[run] Command failed with code {p.returncode}: {cmd}")
        sys.exit(p.returncode)


def main():
    if len(sys.argv) < 2:
        print("Usage: python src\\video_pipeline.py path_to_video.mp4")
        sys.exit(2)

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"Video not found: {video_path}")
        sys.exit(2)

    ensure_dirs()
    ensure_roles_csv()

    # VERY IMPORTANT: wipe old transcripts and old actions
    cleanup_previous_run()

    # Transcript file name = video file name (without extension)
    out_txt = RAW_DIR / f"{video_path.stem}.txt"

    # 1) Transcribe video to meeting transcript
    transcribe_with_whisper(video_path, out_txt)

    # 2) Train ML model (uses data/raw/AMI)
    run_python("src/train_ml.py")

    # 3) Run ML+rules inference to write JSON
    run_python("src/infer_ml.py")

    print(f"[done] Video -> transcript -> actions JSON: {DEFAULT_OUTPUT_JSON}")


if __name__ == "__main__":
    main()


#one note for you guys, one task in to do list is to improve error handling for corrupted video files we can think about it # Updated 
# Updated 
# Updated 
# Updated 
