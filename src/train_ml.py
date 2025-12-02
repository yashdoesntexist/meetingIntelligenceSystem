from __future__ import annotations
from pathlib import Path
from typing import List

import typer
from rich import print
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import joblib

from config import RAW_DIR, DEFAULT_MODEL_PATH
from ami_loader import load_meeting
from action_rules import extract_task_and_deadline
from utils import iter_meeting_files

app = typer.Typer()


@app.command()
def main(
    input_dir: str = typer.Option(str(RAW_DIR), "--input-dir", "--input_dir"),
    model_path: str = typer.Option(str(DEFAULT_MODEL_PATH), "--model-path", "--model_path"),
):
    input_path = Path(input_dir)

    X: List[str] = []
    y: List[int] = []

    for p in iter_meeting_files(input_path):
        meeting = load_meeting(p, input_path / "roles.csv")
        for utt in meeting.utterances:
            X.append(utt.text)
            label = 1 if extract_task_and_deadline(utt.text) else 0
            y.append(label)

    if not X:
        print("[yellow]No data found. Put transcripts in data/raw/AMI.[/yellow]")
        return

    pos = sum(y)
    neg = len(y) - pos
    print(f"[cyan]Training data: {len(X)} utterances (pos={pos}, neg={neg})[/cyan]")

    # If we don't have both classes, skip ML (rules only)
    if len(set(y)) < 2:
        print("[yellow]Not enough class variety. Skipping ML training, rules-only mode.[/yellow]")
        # If a previous model exists, you can optionally delete it or overwrite
        return

    # If classes are very imbalanced, avoid stratification errors
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        do_report = True
    except ValueError:
        # fall back to no test split
        X_train, y_train = X, y
        X_test, y_test = [], []
        do_report = False
        print("[yellow]Not enough examples for stratified split. Training on all data.[/yellow]")

    clf = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )

    clf.fit(X_train, y_train)

    if do_report and X_test:
        y_pred = clf.predict(X_test)
        print(classification_report(y_test, y_pred))

    joblib.dump(clf, model_path)
    print(f"[green]Saved model -> {model_path}[/green]")


if __name__ == "__main__":
    app()
