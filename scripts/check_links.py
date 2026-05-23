import re
from pathlib import Path

import requests


README = Path("README.md")
TIMEOUT = 15


def clean_url(url: str) -> str:
    """Remove Markdown trailing characters while preserving valid URL parentheses."""
    url = url.strip()
    url = url.rstrip(".,;:*")

    # Markdown links often leave one extra closing parenthesis at the end.
    # Keep valid parentheses inside URLs such as Cell IDs: S2542-4351(24)00353-2
    while url.endswith(")") and url.count(")") > url.count("("):
        url = url[:-1].rstrip(".,;:*")

    return url


text = README.read_text(encoding="utf-8")

raw_urls = re.findall(r"https?://[^\s\]<>\"']+", text)
urls = sorted({clean_url(u) for u in raw_urls if clean_url(u)})

print(f"Found {len(urls)} unique URLs\n")

for url in urls:
    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        if response.status_code in [403, 405, 418, 429]:
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=TIMEOUT,
                stream=True,
                headers={"User-Agent": "Mozilla/5.0"},
            )

        status = response.status_code
        final_url = response.url

        if status < 400:
            result = "OK"
        elif status in [403, 418, 429]:
            result = "BLOCKED"
        else:
            result = "CHECK"

        print(f"{result:8} {status:3} {url}")
        if final_url != url:
            print(f"         -> {final_url}")

    except Exception as exc:
        print(f"ERROR        {url}")
        print(f"             {type(exc).__name__}: {exc}")
