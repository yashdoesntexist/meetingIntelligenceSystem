import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import subprocess
import sys
from pathlib import Path
from config import ROOT, RAW_DIR, DEFAULT_OUTPUT_JSON

class App:
    def __init__(self, root):
        self.root = root
        root.title("Meeting Intel GUI")
        root.geometry("850x600")

        ttk.Label(root, text="Meeting Intelligence System", font=("Helvetica", 20, "bold")).pack(pady=10)

        frame = ttk.Frame(root)
        frame.pack(pady=10)

        ttk.Button(frame, text="Process Video File", width=40, command=self.process_video).grid(row=0, column=0, pady=6)
        ttk.Button(frame, text="Re-run on Existing Transcripts", width=40, command=self.process_transcripts_only).grid(row=1, column=0, pady=6)
        ttk.Button(frame, text="Show Action Items", width=40, command=self.show_actions).grid(row=2, column=0, pady=6)
        ttk.Button(frame, text="Show Transcript", width=40, command=self.show_transcript).grid(row=3, column=0, pady=6)
        ttk.Button(frame, text="Exit", width=40, command=root.quit).grid(row=4, column=0, pady=6)

        ttk.Label(root, text="Output:", font=("Helvetica", 14)).pack()

        self.output = tk.Text(root, height=20, wrap=tk.WORD, font=("Consolas", 11))
        self.output.pack(fill="both", expand=True, padx=10, pady=10)

    def write(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state="disabled")

    def run(self, cmd, cwd):
        try:
            subprocess.run(cmd, check=True, cwd=cwd)
            return True
        except:
            messagebox.showerror("Error", "A subprocess failed.")
            return False

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
            messagebox.showerror("Error", "process_video.bat not found.")
            return

        self.write(f"Processing {name}...")
        if self.run([str(bat), name], ROOT):
            self.write("Processing complete.\n")
            self.show_actions()

    def process_transcripts_only(self):
        if messagebox.askyesno("Confirm", "Re-run on transcripts only?") is False:
            return

        self.write("Training model...")
        if not self.run([sys.executable, "src/train_ml.py"], ROOT):
            return

        self.write("Running inference...")
        if not self.run([sys.executable, "src/infer_ml.py"], ROOT):
            return

        self.write("Done.\n")
        self.show_actions()

    def show_actions(self):
        path = Path(DEFAULT_OUTPUT_JSON)
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.config(state="disabled")

        if not path.exists():
            self.write("actions.json not found.")
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        if not data:
            self.write("No action items found.")
            return

        for i, item in enumerate(data, 1):
            self.write(f"{i}. [meeting: {item.get('meeting')} | speaker: {item.get('speaker')}]")
            self.write(f"   action: {item.get('action_item')}")
            if item.get("deadline_text"):
                self.write(f"   deadline: {item.get('deadline_text')} (ISO: {item.get('deadline_iso')})")
            self.write("")

    def show_transcript(self):
        files = list(Path(RAW_DIR).glob("video*.txt"))
        if not files:
            messagebox.showinfo("Info", "No transcript files found.")
            return

        if len(files) == 1:
            f = files[0]
        else:
            win = tk.Toplevel(self.root)
            win.title("Select Transcript")
            lb = tk.Listbox(win, width=40, height=10)
            lb.pack(padx=10, pady=10)

            for x in files:
                lb.insert(tk.END, x.name)

            def choose():
                sel = lb.curselection()
                if not sel:
                    return
                nonlocal f
                f = files[sel[0]]
                win.destroy()

            ttk.Button(win, text="Open", command=choose).pack(pady=5)
            win.grab_set()
            win.wait_window()

        content = f.read_text(encoding="utf-8")
        self.output.config(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, content)
        self.output.config(state="disabled")

root = tk.Tk()
App(root)
root.mainloop()
