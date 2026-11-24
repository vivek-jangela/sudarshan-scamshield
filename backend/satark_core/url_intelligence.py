
import requests
import socket
import ipaddress
try:
    import tldextract
except ImportError:
    tldextract = None
import base64
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone

# VirusTotal is optional. Set this to an API key only when you want to enable it.
VT_API_KEY = None


def get_domain(url):

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        return None

    if tldextract is None:
        from url_features import _split
        _s, _n, _x = _split(hostname)
        return (_n + "." + _x) if _x else hostname

    extracted = tldextract.extract(hostname)

    if not extracted.domain or not extracted.suffix:
        return hostname

    return extracted.domain + "." + extracted.suffix


def is_public_domain(hostname):

    try:
        addresses = socket.getaddrinfo(
            hostname, None, type=socket.SOCK_STREAM
        )

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                return False

        return True

    except Exception:
        return False


def check_domain_age(url):

    domain = get_domain(url)

    if not domain:
        return {"domain": None, "status": "Invalid domain"}

    try:
        response = requests.get(
            f"https://rdap.org/domain/{domain}",
            timeout=15
        )

        if response.status_code != 200:
            return {
                "domain": domain,
                "status": "Registration data unavailable"
            }

        data = response.json()

        creation_date = None

        for event in data.get("events", []):
            if event.get("eventAction") == "registration":
                creation_date = event.get("eventDate")
                break

        if not creation_date:
            return {
                "domain": domain,
                "status": "Creation date unavailable"
            }

        created = datetime.fromisoformat(
            creation_date.replace("Z", "+00:00")
        )

        age_days = (
            datetime.now(timezone.utc) - created
        ).days

        return {
            "domain": domain,
            "creation_date": creation_date,
            "domain_age_days": age_days,
            "status": "Success"
        }

    except Exception as e:
        return {
            "domain": domain,
            "status": "Lookup failed",
            "error": str(e)
        }


def check_redirects(url, max_redirects=5):

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    current_url = url
    redirect_chain = []

    headers = {
        "User-Agent": "SATARK-NETRA-Security-Scanner/1.0"
    }

    for step in range(max_redirects + 1):

        parsed = urlparse(current_url)
        hostname = parsed.hostname

        if parsed.scheme not in ("http", "https") or not hostname:
            return {
                "redirect_chain": redirect_chain,
                "status": "Blocked: invalid URL scheme or host"
            }

        if not is_public_domain(hostname):
            return {
                "redirect_chain": redirect_chain,
                "status": "Blocked: non-public or unresolved host"
            }

        try:
            response = requests.get(
                current_url,
                headers=headers,
                timeout=10,
                allow_redirects=False,
                stream=True
            )

            redirect_chain.append({
                "url": current_url,
                "status_code": response.status_code
            })

            location = response.headers.get("Location")
            response.close()

            if response.status_code not in (301, 302, 303, 307, 308):
                return {
                    "redirect_chain": redirect_chain,
                    "final_url": current_url,
                    "redirect_count": len(redirect_chain) - 1,
                    "status": "Completed"
                }

            if not location:
                break

            current_url = urljoin(current_url, location)

        except Exception as e:
            return {
                "redirect_chain": redirect_chain,
                "status": "Request failed",
                "error": str(e)
            }

    return {
        "redirect_chain": redirect_chain,
        "status": "Maximum redirects reached"
    }


def check_https(url):

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)

    if parsed.scheme != "https":
        return {
            "https_enabled": False,
            "ssl_certificate_valid": None,
            "status": "HTTPS not used"
        }

    if not is_public_domain(parsed.hostname):
        return {
            "https_enabled": True,
            "ssl_certificate_valid": None,
            "status": "Blocked: non-public or unresolved host"
        }

    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=False,
            stream=True
        )

        response.close()

        return {
            "https_enabled": True,
            "ssl_certificate_valid": True,
            "status": "HTTPS connection and certificate verified"
        }

    except requests.exceptions.SSLError:
        return {
            "https_enabled": True,
            "ssl_certificate_valid": False,
            "status": "SSL certificate verification failed"
        }

    except Exception as e:
        return {
            "https_enabled": True,
            "ssl_certificate_valid": None,
            "status": "Connection check failed",
            "error": str(e)
        }


def check_virustotal(url):

    if not VT_API_KEY:
        return {
            "status": "Skipped",
            "reason": "VirusTotal API is disabled"
        }

    # API integration can be enabled later
    return {
        "status": "Not configured"
    }


def analyze_url_intelligence(url):

    domain = get_domain(url)

    if not domain:
        return {
            "url": url,
            "status": "Invalid URL"
        }

    parsed = urlparse(
        url if url.startswith(("http://", "https://"))
        else "http://" + url
    )

    hostname = parsed.hostname

    if not hostname or not is_public_domain(hostname):
        return {
            "url": url,
            "domain": domain,
            "status": "Private, invalid or unreachable domain",
            "domain_age": {"status": "Skipped"},
            "redirect_analysis": {"status": "Skipped"},
            "https_analysis": {"status": "Skipped"},
            "virustotal_analysis": check_virustotal(url)
        }

    result = {
        "url": url,
        "domain": domain,
        "status": "Analysis completed",

        "domain_age": check_domain_age(url),

        "redirect_analysis": check_redirects(url),

        "https_analysis": check_https(url),

        "virustotal_analysis": check_virustotal(url)
    }

    return result


def calculate_intelligence_risk(intelligence):

    score = 0
    indicators = []

    # 1. Domain age check
    age_data = intelligence.get("domain_age", {})

    if age_data.get("status") == "Success":
        age = age_data.get("domain_age_days")

        if age is not None and age < 30:
            score += 20
            indicators.append("Very recently registered domain")

    # 2. Redirect check
    redirect_data = intelligence.get("redirect_analysis", {})

    if redirect_data.get("status") == "Completed":
        redirects = redirect_data.get("redirect_count", 0)

        if redirects > 2:
            score += 15
            indicators.append("Multiple redirects detected")

    # 3. SSL certificate check
    ssl_data = intelligence.get("https_analysis", {})

    if ssl_data.get("ssl_certificate_valid") is False:
        score += 20
        indicators.append("Invalid SSL certificate")

    # 4. VirusTotal check
    vt_data = intelligence.get("virustotal_analysis", {})

    if vt_data.get("status") in ("Analysis found", "Success"):
        detections = vt_data.get("malicious", 0)

        if detections >= 2:
            score += 35
            indicators.append("Flagged by multiple security engines")

    if score >= 40:
        level = "HIGH"
    elif score >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "intelligence_risk_score": score,
        "intelligence_risk_level": level,
        "indicators": indicators
    }
