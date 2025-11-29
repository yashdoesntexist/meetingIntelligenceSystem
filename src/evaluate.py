from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from config import PROCESSED_DIR

PRED = PROCESSED_DIR / "actions.json"
GOLD = PROCESSED_DIR / "gold.json"

def normalize(s: str) -> str:
    return " ".join(s.lower().split())
#  creating action.json file
def main():
    if not PRED.exists() or not GOLD.exists():
        print("Missing predictions or gold. Create data/processed/gold.json first.")
        return                      
    pred = pd.read_json(PRED)
    gold = pd.read_json(GOLD)
    pred["key"] = pred["assignee"].fillna("").map(normalize) + " | " + pred["action_item"].fillna("").map(normalize)
    gold["key"] = gold["assignee"].fillna("").map(normalize) + " | " + gold["action_item"].fillna("").map(normalize)
    tp = len(set(pred["key"]) & set(gold["key"]))
    fp = len(set(pred["key"]) - set(gold["key"]))
    fn = len(set(gold["key"]) - set(pred["key"]))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    print(f"Precision: {prec:.3f}\nRecall:    {rec:.3f}\nF1:        {f1:.3f}")

if __name__ == "__main__":
    main()
