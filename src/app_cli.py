from __future__ import annotations
import subprocess
import json
from pathlib import Path
import sys

from config import ROOT, RAW_DIR, DEFAULT_OUTPUT_JSON


def print_header():
    print("=" * 70)
    print("  MEETING INTEL (COMP 482) - INTERACTIVE MENU")
    print("=" * 70)
    print()


def pause():
    input("\nPress ENTER to continue...")



def show_actions():
    out_path = Path(DEFAULT_OUTPUT_JSON)
    if not out_path.exists():
        print("No actions.json found. Run processing first.")
        return

    data = json.loads(out_path.read_text(encoding="utf-8"))
    if not data:
        print("No action items detected.")
        return

    print(f"\nFound {len(data)} action item(s):\n")
    for i, item in enumerate(data, start=1):
        print(f"{i}. [meeting: {item.get('meeting')} | speaker: {item.get('speaker')}]")
        print(f"   action: {item.get('action_item')}")
        if item.get("deadline_text"):
            print(f"   deadline: {item.get('deadline_text')}  (ISO: {item.get('deadline_iso')})")
        print()



def show_transcript():
    print("\n=== Show Transcript ===")

    candidates = list(Path(RAW_DIR).glob("video*.txt"))

    if not candidates:
        print("No transcript found. Process a video first.")
        return

    if len(candidates) == 1:
        transcript_file = candidates[0]
    else:
        print("\nMultiple transcripts found:")
        for i, f in enumerate(candidates, start=1):
            print(f"{i}) {f.name}")
        choice = input("\nChoose transcript number: ").strip()

        try:
            choice = int(choice)
            transcript_file = candidates[choice - 1]
        except Exception:
            print("Invalid choice.")
            return

    print(f"\nShowing transcript: {transcript_file.name}\n")
    print("-" * 70)

    content = transcript_file.read_text(encoding="utf-8").strip()
    print(content)

    print("-" * 70)
    print("\nEnd of transcript.")


def process_video():
    print("\n=== Process a video file ===")
    print("Put your .mp4 file in the project folder, e.g.:")
    print(str(ROOT / "video2.mp4"))
    video_name = input("Enter video file name (e.g., video2.mp4): ").strip()

    if not video_name:
        print("No file name given.")
        return

    video_path = ROOT / video_name
    if not video_path.exists():
        print(f"File not found: {video_path}")
        return

    print(f"\nRunning pipeline on: {video_path.name}")

    bat = ROOT / "scripts" / "process_video.bat"
    if not bat.exists():
        print(f"Batch script not found: {bat}")
        return

    try:
        subprocess.run(
            [str(bat), video_path.name],
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running process_video.bat: {e}")
        return

    print("\nVideo processed. Current actions.json:")
    show_actions()



def process_transcripts_only():
    print("\n=== Re-run on transcripts only (no new video) ===")
    print(f"Transcripts folder: {RAW_DIR}")

    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    print("\nTraining ML model on current transcripts...")
    try:
        subprocess.run(
            [sys.executable, "src/train_ml.py"],
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running train_ml.py: {e}")
        return


    print("\nRunning inference...")
    try:
        subprocess.run(
            [sys.executable, "src/infer_ml.py"],
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running infer_ml.py: {e}")
        return

    print("\nDone. Current actions.json:")
    show_actions()



def main_menu():
    while True:
        print_header()
        print("Choose an option:")
        print("  1) Process a video file (transcribe + train + infer)")
        print("  2) Re-run on existing transcripts only (train + infer)")
        print("  3) Show current action items (actions.json)")
        print("  4) Show full transcript of video")
        print("  0) Exit")
        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            process_video()
            pause()
        elif choice == "2":
            process_transcripts_only()
            pause()
        elif choice == "3":
            show_actions()
            pause()
        elif choice == "4":
            show_transcript()
            pause()
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")
            pause()


if __name__ == "__main__":
    main_menu()
