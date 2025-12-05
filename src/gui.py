import tkinter as tk
from tkinter import filedialog, messagebox
import json
import subprocess
import sys
from pathlib import Path
from threading import Thread
from config import ROOT, RAW_DIR, DEFAULT_OUTPUT_JSON


class App:
    def __init__(self, root):
        self.root = root
        root.title("Meeting Intelligence System")
        root.geometry("900x650")
        root.configure(bg="#0d0d0d")

        header = tk.Label(root, text="Meeting Intelligence System",
                          font=("Helvetica", 24, "bold"),
                          fg="white", bg="#0d0d0d")
        header.pack(anchor="w", padx=20, pady=(20, 5))

        sub = tk.Label(root, text="Dashboard",
                       font=("Helvetica", 14),
                       fg="#bfbfbf", bg="#0d0d0d")
        sub.pack(anchor="w", padx=20, pady=(0, 20))

        # Buttons
        btn_frame = tk.Frame(root, bg="#0d0d0d")
        btn_frame.pack(fill="x", padx=20, pady=10)

        tk.Button(btn_frame, text="Process Video File", width=25, height=2,
                  command=lambda: Thread(target=self.process_video).start()).grid(row=0, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="Re-run Transcripts", width=25, height=2,
                  command=lambda: Thread(target=self.process_transcripts_only).start()).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(btn_frame, text="Show Action Items", width=25, height=2,
                  command=self.show_actions).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="Show Transcript", width=25, height=2,
                  command=self.show_transcript).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(btn_frame, text="Exit", width=52, height=2,
                  command=root.quit).grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        # Output
        out_lbl = tk.Label(root, text="Output",
                           font=("Helvetica", 14),
                           fg="#bfbfbf", bg="#0d0d0d")
        out_lbl.pack(anchor="w", padx=20, pady=(10, 5))

        self.output = tk.Text(root,
                              height=20,
                              wrap=tk.WORD,
                              font=("Consolas", 12),
                              bg="#111111",
                              fg="white",
                              insertbackground="white")
        self.output.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # ---------------- Utility ----------------
    def write(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state="disabled")
        self.root.update()  # immediate update so messages appear

    def run_subprocess(self, cmd, cwd):
        try:
            process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.write(line.strip())
            process.wait()
            if process.returncode != 0:
                self.write(f"Process exited with code {process.returncode}")
        except Exception as e:
            self.write(f"Error running command: {e}")


    def process_video(self):
        video_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
        if not video_path:
            return
        name = Path(video_path).name
        dest = ROOT / name
        if Path(video_path) != dest:
            dest.write_bytes(Path(video_path).read_bytes())
        bat = ROOT / "scripts" / "process_video.bat"
        if not bat.exists():
            self.write("Error: process_video.bat not found!")
            return
        self.write(f"Processing video: {name} ...")
        self.run_subprocess([str(bat), name], ROOT)
        self.write("Video processing complete.")
        self.show_actions()

    def process_transcripts_only(self):
        self.write("Re-running on transcripts...")
        self.write("Training...")
        self.run_subprocess([sys.executable, "src/train_ml.py"], ROOT)
        self.write("Inference...")
        self.run_subprocess([sys.executable, "src/infer_ml.py"], ROOT)
        self.write("Done. Showing updated action items.")
        self.show_actions()

    def show_actions(self):
        self.output.delete("1.0", "end")
        self.write("Loading action items...")
        path = Path(DEFAULT_OUTPUT_JSON)
        if not path.exists():
            self.write(f"Actions file not found: {path}")
            return
        try:
            data = json.loads(path.read_text())
        except Exception as e:
            self.write(f"Failed to read JSON: {e}")
            return
        if not data:
            self.write("No action items found.")
            return
        self.write(f"Loaded {len(data)} action items:\n")
        for i, item in enumerate(data, 1):
            self.write(f"{i}. [{item.get('meeting')} | {item.get('speaker')}]")
            self.write(f"   action: {item.get('action_item')}")
            if item.get("deadline_text"):
                self.write(f"   deadline: {item.get('deadline_text')} ({item.get('deadline_iso')})")
            self.write("")
        self.write("Action items loaded successfully. Select next action.")

    def show_transcript(self):
        self.output.delete("1.0", "end")
        self.write("Loading transcripts...")
        files = sorted(Path(RAW_DIR).glob("video*.txt"))
        if not files:
            self.write(f"No transcript files found in {RAW_DIR}")
            return
        for idx, f in enumerate(files, 1):
            self.write(f"--- Transcript {idx}: {f.name} ---\n")
            try:
                content = f.read_text()
                self.write(content + "\n")
            except Exception as e:
                self.write(f"Failed to read {f.name}: {e}")
        self.write("Transcripts loaded successfully.")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
