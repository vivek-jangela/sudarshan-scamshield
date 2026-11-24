"""SQLite storage: cases, extracted identifiers, heat-list, linking graph. Shape matches what the React UI expects."""
import json
import sqlite3
import datetime
from . import config

LINKABLE = ("domain", "phone", "upi", "package", "crypto", "email", "ip", "bank_account", "cert")
SCHEMA = """
CREATE TABLE IF NOT EXISTS cases(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  kind TEXT NOT NULL,
  channel TEXT, source TEXT, reporter TEXT, status TEXT DEFAULT 'new',
  title TEXT, verdict TEXT, level TEXT, score REAL, advice TEXT,
  content TEXT, evidence_sha256 TEXT,
  indicators TEXT, info TEXT
);
CREATE TABLE IF NOT EXISTS identifiers(
  case_id INTEGER NOT NULL, type TEXT NOT NULL, value TEXT NOT NULL,
  UNIQUE(case_id, type, value)
);
CREATE INDEX IF NOT EXISTS ix_id_val ON identifiers(type, value);
CREATE INDEX IF NOT EXISTS ix_case_level ON cases(level);
"""


def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def add_case(rec: dict) -> int:
    """rec keys: kind, channel, source, reporter, title, verdict, level, score(0-1), advice, content,
    evidence_sha256, indicators(list), info(dict), identifiers(dict type -> [values])."""
    with conn() as c:
        cur = c.execute(
            "INSERT INTO cases(created_at,kind,channel,source,reporter,status,title,verdict,level,score,advice,content,"
            "evidence_sha256,indicators,info) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_now(), rec["kind"], rec.get("channel"), rec.get("source"), rec.get("reporter", "citizen"), "new",
             rec.get("title"), rec.get("verdict"), rec["level"], rec["score"], rec.get("advice"), rec.get("content"),
             rec.get("evidence_sha256"), json.dumps(rec.get("indicators", []), ensure_ascii=False),
             json.dumps(rec.get("info", {}), ensure_ascii=False, default=str)))
        cid = cur.lastrowid
        for t, vals in (rec.get("identifiers") or {}).items():
            for v in vals:
                c.execute("INSERT OR IGNORE INTO identifiers VALUES(?,?,?)", (cid, t, str(v)))
    return cid


def _row_to_case(r, ids):
    d = dict(r)
    d["case_id"] = d["id"]
    d["indicators"] = json.loads(d["indicators"] or "[]")
    d["info"] = json.loads(d["info"] or "{}")
    d["identifiers"] = ids
    return d


def get_identifiers(cid):
    out = {}
    with conn() as c:
        for r in c.execute("SELECT type,value FROM identifiers WHERE case_id=? ORDER BY type,value", (cid,)):
            out.setdefault(r["type"], []).append(r["value"])
    return out


def get_case(cid):
    with conn() as c:
        r = c.execute("SELECT * FROM cases WHERE id=?", (cid,)).fetchone()
    return _row_to_case(r, get_identifiers(cid)) if r else None


def set_status(cid, status):
    with conn() as c:
        c.execute("UPDATE cases SET status=? WHERE id=?", (status, cid))


def list_cases(q="", level="", kind="", limit=300):
    sql = ("SELECT DISTINCT c.id,c.created_at,c.kind,c.title,c.verdict,c.level,c.score FROM cases c "
           "LEFT JOIN identifiers i ON i.case_id=c.id WHERE 1=1")
    a = []
    if q:
        sql += " AND (c.title LIKE ? OR c.content LIKE ? OR c.verdict LIKE ? OR i.value LIKE ?)"
        a += [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q.lower()}%"]
    if level:
        sql += " AND c.level=?"; a.append(level.capitalize())
    if kind:
        sql += " AND c.kind=?"; a.append(kind)
    sql += " ORDER BY c.id DESC LIMIT ?"; a.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(sql, a)]


def cases_by_identifier(itype, value, exclude=None, only_flagged=False, limit=10):
    sql = ("SELECT DISTINCT c.id,c.title,c.level,c.verdict FROM identifiers i JOIN cases c ON c.id=i.case_id "
           "WHERE i.type=? AND i.value=?")
    a = [itype, value]
    if exclude:
        sql += " AND c.id!=?"; a.append(exclude)
    if only_flagged:
        sql += " AND c.level IN ('High','Medium')"
    sql += " ORDER BY c.id DESC LIMIT ?"; a.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(sql, a)]


def prior_reports(ids: dict):
    """For the blacklist: how many Medium/High cases already contain each identifier."""
    out = []
    with conn() as c:
        for t, vals in ids.items():
            if t not in LINKABLE:
                continue
            for v in vals:
                n = c.execute("SELECT COUNT(DISTINCT i.case_id) FROM identifiers i JOIN cases c ON c.id=i.case_id "
                              "WHERE i.type=? AND i.value=? AND c.level IN ('High','Medium')", (t, v)).fetchone()[0]
                if n:
                    out.append((t, v, n))
    return out


def heatlist(itype="", limit=50):
    marks = ",".join("?" * len(LINKABLE))
    sql = (f"SELECT i.type,i.value,COUNT(DISTINCT i.case_id) AS reports FROM identifiers i JOIN cases c ON c.id=i.case_id "
           f"WHERE c.level IN ('High','Medium') AND i.type IN ({marks})")
    a = list(LINKABLE)
    if itype:
        sql += " AND i.type=?"; a.append(itype)
    sql += " GROUP BY i.type,i.value ORDER BY reports DESC, i.value LIMIT ?"; a.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(sql, a)]


def graph():
    """Identifiers shared by 2+ flagged cases: one scammer reused across messages, apps and websites."""
    marks = ",".join("?" * len(LINKABLE))
    sql = (f"SELECT i.type,i.value,GROUP_CONCAT(DISTINCT i.case_id) AS cs FROM identifiers i JOIN cases c ON c.id=i.case_id "
           f"WHERE c.level IN ('High','Medium') AND i.type IN ({marks}) GROUP BY i.type,i.value "
           f"HAVING COUNT(DISTINCT i.case_id)>=2 ORDER BY COUNT(DISTINCT i.case_id) DESC, i.value")
    with conn() as c:
        return [{"type": r["type"], "value": r["value"], "cases": sorted(int(x) for x in r["cs"].split(","))}
                for r in c.execute(sql, list(LINKABLE))]


def links(cid):
    """Other flagged cases sharing at least one identifier with this case."""
    marks = ",".join("?" * len(LINKABLE))
    sql = (f"SELECT o.case_id AS case_id, i.type AS shared_type, i.value AS shared_value, c.title, c.level "
           f"FROM identifiers i JOIN identifiers o ON o.type=i.type AND o.value=i.value AND o.case_id!=i.case_id "
           f"JOIN cases c ON c.id=o.case_id WHERE i.case_id=? AND c.level IN ('High','Medium') AND i.type IN ({marks})")
    with conn() as c:
        rows = [dict(r) for r in c.execute(sql, [cid] + list(LINKABLE))]
    cases = {}
    for r in rows:
        cases.setdefault(r["case_id"], {"id": r["case_id"], "title": r["title"], "level": r["level"]})
    return {"linked_cases": list(cases.values()),
            "edges": [{"case_id": r["case_id"], "shared_type": r["shared_type"], "shared_value": r["shared_value"]} for r in rows]}


def contents_for_similarity(kind, limit=1500):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id,title,level,content FROM cases WHERE kind=? ORDER BY id DESC LIMIT ?", (kind, limit))]


def stats():
    with conn() as c:
        total = c.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        by = {r[0]: r[1] for r in c.execute("SELECT level,COUNT(*) FROM cases GROUP BY level")}
        kinds = {r[0]: r[1] for r in c.execute("SELECT kind,COUNT(*) FROM cases GROUP BY kind")}
    return {"total": total, "high": by.get("High", 0), "medium": by.get("Medium", 0), "low": by.get("Low", 0), "by_kind": kinds}
