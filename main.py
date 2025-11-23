
import json
from processors.transcript_loader import load_transcript
from processors.diarization import identify_speakers
from processors.action_extraction import extract_actions


def run_pipeline(transcript_path: str, output_path: str = "output/results.json"):
    print("[1] Loading transcript...")
    raw = load_transcript(transcript_path)

    print("[2] Identifying speakers...")
    structured = identify_speakers(raw)

    print("[3] Extracting action items...")
    actions = extract_actions(structured)

    output = {
        "total_segments": len(structured),
        "action_items": actions
    }

    print("[4] Saving JSON output...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print(f"Done! Results saved to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Meeting Intelligence MVP")
    parser.add_argument("--file", required=True, help="Path to transcript .txt file")
    parser.add_argument("--out", default="output/results.json")

    args = parser.parse_args()

    run_pipeline(args.file, args.out)
