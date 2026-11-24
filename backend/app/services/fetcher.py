"""Safe page fetching for website analysis. Blocks private / internal addresses (SSRF), caps size, follows few redirects.
Static analysis only: the page is downloaded as text and never executed."""
import requests
from urllib.parse import urlparse, urljoin
from .. import config
from . import core

UA = {"User-Agent": "ScamShield-Analyzer/1.0 (+static analysis; Rajasthan Police hackathon prototype)"}


class FetchError(Exception):
    pass


def fetch_page(url, max_bytes=None, allowed_hosts=None, max_redirects=3):
    max_bytes = max_bytes or config.MAX_HTML_BYTES
    cur = url if "://" in url else "http://" + url
    for _ in range(max_redirects + 1):
        p = urlparse(cur)
        if p.scheme not in ("http", "https") or not p.hostname:
            raise FetchError("Only http/https addresses can be fetched.")
        if allowed_hosts and p.hostname not in allowed_hosts:
            raise FetchError("Host not allowed.")
        if not core.url_intelligence.is_public_domain(p.hostname):
            raise FetchError("Address is private, internal or does not resolve; not fetched.")
        try:
            r = requests.get(cur, headers=UA, timeout=10, allow_redirects=False, stream=True)
        except requests.RequestException as e:
            raise FetchError(f"Could not reach the site: {type(e).__name__}")
        if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
            cur = urljoin(cur, r.headers["Location"]); r.close(); continue
        buf = b""
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) >= max_bytes:
                break
        r.close()
        ctype = r.headers.get("Content-Type", "")
        if ctype and not any(t in ctype.lower() for t in ("html", "text", "xml", "json")):
            raise FetchError(f"Not a web page (content type {ctype.split(';')[0]}).")
        enc = r.encoding or "utf-8"
        return {"html": buf.decode(enc, "replace"), "final_url": cur, "status_code": r.status_code}
    raise FetchError("Too many redirects.")
