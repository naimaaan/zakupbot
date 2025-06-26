import os
import json

TRU_TRACK_FILE = "storage/tru_rows.json"
os.makedirs("storage", exist_ok=True)

def load_tru_data() -> dict:
    if not os.path.exists(TRU_TRACK_FILE):
        return {}
    with open(TRU_TRACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tru_data(data: dict):
    with open(TRU_TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_new_tru_row(bin_number: str, tru_code: str, row_text: str, data: dict) -> bool:
    bin_data = data.get(bin_number, {})
    known_rows = bin_data.get(tru_code, [])
    return row_text not in known_rows

def add_tru_row(bin_number: str, tru_code: str, row_text: str, data: dict):
    if bin_number not in data:
        data[bin_number] = {}
    if tru_code not in data[bin_number]:
        data[bin_number][tru_code] = []
    if row_text not in data[bin_number][tru_code]:
        data[bin_number][tru_code].append(row_text)
