"""Repeat-content detection: TF-IDF cosine similarity between a case and earlier cases of the same kind.
Numbers, phones and links are normalised first (same normaliser as the message model) so template-based scam campaigns match."""
from .. import db
from . import core


def _norm(t):
    import msg_text  # from satark_core
    return msg_text.norm(t or "")


def similar_cases(cid, threshold=0.55, limit=5):
    case = db.get_case(cid)
    if not case or case["kind"] not in ("message", "website"):
        return []
    rows = db.contents_for_similarity(case["kind"])
    if len(rows) < 2:
        return []
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    texts = [_norm(r["content"]) for r in rows]
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit_transform(texts)
    except ValueError:  # empty vocabulary
        return []
    idx = next((i for i, r in enumerate(rows) if r["id"] == cid), None)
    if idx is None:
        return []
    sims = linear_kernel(vec[idx], vec).ravel()
    out = [{"id": rows[i]["id"], "title": rows[i]["title"], "level": rows[i]["level"], "similarity": round(float(s), 2)}
           for i, s in enumerate(sims) if i != idx and s >= threshold]
    return sorted(out, key=lambda x: -x["similarity"])[:limit]
