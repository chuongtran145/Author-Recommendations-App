# data_loader.py
import pandas as pd, re
from collections import Counter
from typing import Optional

def parse_year_like(x) -> Optional[int]:
    if pd.isna(x): return None
    s = str(x)
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        try: return int(m.group(0))
        except: return None
    try: return int(float(s))
    except: return None

def pick_split_year(csv_path: str, year_col: str, train_frac: float = 0.8, chunksize: int = 20000) -> Optional[int]:
    counts = Counter()
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, dtype=str):
        if year_col not in chunk.columns: continue
        yrs = chunk[year_col].map(parse_year_like).dropna().astype(int)
        counts.update(yrs.values.tolist())
    if not counts: return None
    total = sum(counts.values()); target = total * train_frac; cum = 0
    for y, cnt in sorted(counts.items()):
        cum += cnt
        if cum >= target: return y
    return max(counts.keys())
