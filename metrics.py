# metrics.py
import math
from typing import Dict, Set, List, Tuple
from collections import Counter as TCounter

Adjacency = Dict[str, TCounter]
AuthorJournals = Dict[str, Set[str]]

def candidate_set(adj: Adjacency, u: str, include_neighbors: bool = False) -> Set[str]:
    neighbors = set(adj[u].keys())
    if include_neighbors: return set(adj.keys()) - {u}
    two_hop = set()
    for x in neighbors: two_hop.update(adj[x].keys())
    two_hop.discard(u)
    return two_hop - neighbors

def common_neighbors_count(adj: Adjacency, u: str, v: str) -> int:
    return len(set(adj[u].keys()) & set(adj[v].keys()))

def adamic_adar(adj: Adjacency, u: str, v: str) -> float:
    inter = set(adj[u].keys()) & set(adj[v].keys()); s = 0.0
    for z in inter:
        deg = len(adj[z])
        if deg > 1: s += 1.0 / math.log(deg)
    return s

def journal_overlap(author_journals: AuthorJournals, u: str, v: str) -> Tuple[Set[str], Set[str], float]:
    Ju = author_journals.get(u, set()); Jv = author_journals.get(v, set())
    inter = Ju & Jv; union = Ju | Jv
    jacc = (len(inter) / len(union)) if union else 0.0
    return inter, union, jacc

def normalize(values: List[float]) -> List[float]:
    if not values: return []
    m = min(values); M = max(values)
    if M <= m: return [0.0 for _ in values]
    return [(x - m) / (M - m) for x in values]
