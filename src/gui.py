import tkinter as tk
from tkinter import filedialog, messagebox
import json
import subprocess
import sys
from pathlib import Path
from config import ROOT, RAW_DIR, DEFAULT_OUTPUT_JSON


def create_round_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1+radius, y1,
        x1+radius, y1,
        x2-radius, y1,
        x2-radius, y1,
        x2, y1,
        x2, y1+radius,
        x2, y1+radius,
        x2, y2-radius,
        x2, y2-radius,
        x2, y2,
        x2-radius, y2,
        x2-radius, y2,
        x1+radius, y2,
        x1+radius, y2,
        x1, y2,
        x1, y2-radius,
        x1, y2-radius,
        x1, y1+radius,
        x1, y1+radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Meeting Intelligence System")
        root.geometry("1100x760")
        root.configure(bg="#0d0d0d")

        header = tk.Label(root, text="Meeting Intelligence System",
                          font=("Helvetica", 28, "bold"),
                          fg="white", bg="#0d0d0d")
        header.pack(anchor="w", padx=40, pady=(25, 5))

        sub = tk.Label(root, text="Dashboard",
                       font=("Helvetica", 14),
                       fg="#bfbfbf", bg="#0d0d0d")
        sub.pack(anchor="w", padx=40, pady=(0, 25))

        container = tk.Frame(root, bg="#0d0d0d")
        container.pack(fill="x", padx=40)


        self.make_tile(container, "Process Video File",
                       "Run full pipeline on a new video",
                       self.process_video).grid(row=0, column=0, padx=20, pady=20)

        self.make_tile(container, "Re-run on Transcripts",
                       "Train + infer on existing transcripts",
                       self.process_transcripts_only).grid(row=0, column=1, padx=20, pady=20)


        self.make_tile(container, "Show Action Items",
                       "View current actions",
                       self.show_actions).grid(row=1, column=0, padx=20, pady=20)

        self.make_tile(container, "Show Transcript",
                       "View processed transcript files",
                       self.show_transcript).grid(row=1, column=1, padx=20, pady=20)


        self.make_tile(container, "Exit",
                       "Close the application",
                       root.quit, wide=True).grid(row=2, column=0, columnspan=2, padx=20, pady=20)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)


        out_lbl = tk.Label(root, text="Output",
                           font=("Helvetica", 14),
                           fg="#bfbfbf", bg="#0d0d0d")
        out_lbl.pack(anchor="w", padx=40, pady=(15, 5))

        self.output = tk.Text(root,
                              height=12,
                              wrap=tk.WORD,
                              font=("Consolas", 12),
                              bg="#111111",
                              fg="white",
                              insertbackground="white",
                              relief="flat",
                              borderwidth=12)
        self.output.pack(fill="both", expand=True, padx=40, pady=(0, 30))

    def make_tile(self, parent, title, desc, command, wide=False):
        w = 460 if wide else 440
        h = 150

        canvas = tk.Canvas(parent,
                           width=w,
                           height=h,
                           bg="#0d0d0d",
                           highlightthickness=0)
        canvas.tile_bg = create_round_rect(canvas,
                                           5, 5, w-5, h-5,
                                           radius=28,
                                           fill="#1a1a1a",
                                           outline="")


        canvas.create_text(40, 45,
                           text=title,
                           anchor="w",
                           fill="white",
                           font=("Helvetica", 18, "bold"))
        canvas.create_text(40, 85,
                           text=desc,
                           anchor="w",
                           fill="#b0b0b0",
                           font=("Helvetica", 12))

        def on_enter(e):
            canvas.itemconfig(canvas.tile_bg, fill="#262626")

        def on_leave(e):
            canvas.itemconfig(canvas.tile_bg, fill="#1a1a1a")


        def on_click(e):
            command()

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)

        return canvas


    def write(self, text):
        self.output.config(state="normal")
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state="disabled")

    def run(self, cmd, cwd):
        try:
            subprocess.run(cmd, check=True, cwd=cwd)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"A subprocess failed:\n{e}")
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
            self.write("Processing complete.")
            self.show_actions()

    def process_transcripts_only(self):
        if not messagebox.askyesno("Confirm", "Re-run on transcripts only?"):
            return
        self.write("Training...")
        if not self.run([sys.executable, "src/train_ml.py"], ROOT): return
        self.write("Inferring...")
        if not self.run([sys.executable, "src/infer_ml.py"], ROOT): return
        self.write("Done.")
        self.show_actions()

    def show_actions(self):
        path = Path(DEFAULT_OUTPUT_JSON)
        self.output.delete("1.0", "end")
        if not path.exists():
            self.write("actions.json not found.")
            return
        data = json.loads(path.read_text())
        if not data:
            self.write("No action items found.")
            return
        for i, item in enumerate(data, 1):
            self.write(f"{i}. [{item.get('meeting')} | {item.get('speaker')}]")
            self.write(f"   action: {item.get('action_item')}")
            if item.get("deadline_text"):
                self.write(f"   deadline: {item.get('deadline_text')} ({item.get('deadline_iso')})")
            self.write("")

    def show_transcript(self):
        files = list(Path(RAW_DIR).glob("video*.txt"))
        if not files:
            messagebox.showinfo("Info", "No transcript files found.")
            return
        f = files[0]
        content = f.read_text()
        self.output.delete("1.0", "end")
        self.output.insert("end", content)


root = tk.Tk()
App(root)
root.mainloop()
