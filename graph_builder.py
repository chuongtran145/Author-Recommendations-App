# graph_builder.py
import pandas as pd
from collections import Counter, defaultdict
from itertools import combinations
from typing import Dict, Set, Tuple
from data_loader import parse_year_like

Adjacency = Dict[str, Counter]
AuthorJournals = Dict[str, Set[str]]
BAD_VENUES = {"", "nan", "none", "null", "n/a", "na", "n.a."}

def split_authors(s: str):
    if not isinstance(s, str): return []
    parts = [p.strip() for p in s.split(";")]
    return list({p for p in parts if p})

def clean_venue(raw):
    if raw is None: return ""
    v = str(raw).strip()
    return "" if v.lower() in BAD_VENUES else v

def build_graph_and_journals(csv_path, authors_col, year_col, venue_col, split_year, max_rows=200000, chunksize=20000) -> Tuple[Adjacency, Set[str], AuthorJournals, int]:
    adj = defaultdict(Counter); author_journals = defaultdict(set); nodes_seen = set(); used_rows = 0
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, dtype=str):
        df = chunk
        if split_year is not None and year_col in df.columns:
            yrs = df[year_col].map(parse_year_like)
            mask = yrs.apply(lambda v: (v is not None and v <= split_year))
            df = df[mask.fillna(False)].copy()
        if authors_col not in df.columns: continue
        for _, row in df.iterrows():
            authors = split_authors(row.get(authors_col, ""))
            venue_val = clean_venue(row.get(venue_col, "")) if venue_col in df.columns else ""
            if len(authors) >= 2:
                for u, v in combinations(authors, 2):
                    adj[u][v] += 1; adj[v][u] += 1; nodes_seen.add(u); nodes_seen.add(v)
            if venue_val:
                for a in authors: author_journals[a].add(venue_val)
        used_rows += len(df)
        if used_rows >= max_rows: break
    return adj, nodes_seen, author_journals, used_rows
