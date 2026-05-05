import re
import requests
import dns.resolver
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def check_website(url, timeout=8):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        if r.status_code >= 400 or r.status_code == 405:
            r = requests.get(url, allow_redirects=True, timeout=timeout)
        return {
            "url": url,
            "valid": r.status_code < 400,
            "status": r.status_code,
            "final_url": r.url,
        }

    except requests.RequestException as e:
        return {
            "url": url,
            "valid": False,
            "error": str(e),
        }


def check_email(email):
    if not EMAIL_RE.match(email):
        return {"email": email, "valid": False, "reason": "bad syntax"}
    domain = email.split("@", 1)[1]
    try:
        dns.resolver.resolve(domain, "MX")
        return {"email": email, "valid": True, "reason": "domain has MX records"}
    except Exception:
        return {"email": email, "valid": False, "reason": "no MX records"}


