# recommender.py
from typing import Dict, Set, List, Optional
from collections import Counter as TCounter
from metrics import candidate_set, common_neighbors_count, adamic_adar, journal_overlap, normalize

Adjacency = Dict[str, TCounter]
AuthorJournals = Dict[str, Set[str]]
BAD_VENUES = {"", "nan", "none", "null", "n/a", "na", "n.a."}

def pick_target(adj: Adjacency, preferred: str) -> str:
    if preferred in adj: return preferred
    low = preferred.lower()
    for n in adj.keys():
        if n.lower() == low: return n
    cand = [n for n in adj.keys() if low in n.lower()]
    if cand: return cand[0]
    best, best_deg = None, -1
    for n, neigh in adj.items():
        d = len(neigh)
        if d > best_deg: best, best_deg = n, d
    return best

def format_explanation(common_journals: List[str], jacc: float, common_neighbors: List[str]) -> str:
    cj = "; ".join(common_journals) if common_journals else "no common journal"
    cn = "; ".join(common_neighbors) if common_neighbors else "no common neighbor"
    return f"Common journals: {cj} (J={jacc:.2f}); Common neighbors: {cn}"

def recommend(adj: Adjacency, author_journals: AuthorJournals, target: str, topk: int, include_neighbors: bool, w_aa: float, w_cn: float, w_jj: float, filter_journals: Optional[Set[str]] = None):
    C = candidate_set(adj, target, include_neighbors=include_neighbors); recs = []; neighbors_target = set(adj[target].keys())
    filter_set = None
    if filter_journals is not None: filter_set = {j.strip().lower() for j in filter_journals if j.strip()}
    for v in C:
        cn = common_neighbors_count(adj, target, v); aa = adamic_adar(adj, target, v)
        inter_j, union_j, jj = journal_overlap(author_journals, target, v)
        clean_journals = [j for j in sorted(list(inter_j)) if j and j.strip().lower() not in BAD_VENUES]
        if not clean_journals: continue
        if filter_set is not None:
            lower_j = {j.strip().lower() for j in clean_journals}
            if not (lower_j & filter_set): continue
        inter_neighbors = list(neighbors_target & set(adj[v].keys()))
        inter_neighbors.sort(key=lambda z: len(adj[z]), reverse=True)
        recs.append((v, cn, aa, jj, clean_journals[:5], inter_neighbors[:5]))
    if not recs: return []
    CNn = normalize([r[1] for r in recs]); AAn = normalize([r[2] for r in recs]); JJn = normalize([r[3] for r in recs])
    scored = []
    for (v, cn, aa, jj, common_journals, common_neighbors), cnv, aav, jjv in zip(recs, CNn, AAn, JJn):
        score = w_aa * aav + w_cn * cnv + w_jj * jjv
        explanation = format_explanation(common_journals, jj, common_neighbors)
        scored.append((v, score, aa, cn, jj, common_journals, common_neighbors, explanation))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:topk]
