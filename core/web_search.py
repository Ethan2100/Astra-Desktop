"""Small dependency-free web search client for ASTRA's first online phase."""
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, parse_qs, unquote
from urllib.request import Request, urlopen
from urllib.error import URLError
import re


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class _DuckDuckGoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._active = None
        self._capture = None
        self._snippet = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "a" and "result__a" in classes:
            self._active = {"title": "", "url": attrs.get("href", "")}
            self._capture = "title"
        elif "result__snippet" in classes:
            self._capture = "snippet"
            self._snippet = ""

    def handle_data(self, data):
        if self._capture == "title" and self._active is not None:
            self._active["title"] += data
        elif self._capture == "snippet":
            self._snippet += data

    def handle_endtag(self, tag):
        if tag == "a" and self._capture == "title" and self._active is not None:
            self.results.append(SearchResult(
                self._active["title"].strip(),
                _clean_result_url(self._active["url"]),
                ""
            ))
            self._active = None
            self._capture = None
        elif self._capture == "snippet" and tag in {"div", "td"}:
            if self.results and not self.results[-1].snippet:
                self.results[-1].snippet = re.sub(r"\\s+", " ", self._snippet).strip()
            self._snippet = ""
            self._capture = None


def _clean_result_url(raw_url):
    if not raw_url:
        return ""
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    parsed = urlparse(raw_url)
    if "duckduckgo.com" in parsed.netloc:
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    return raw_url


class WebSearch:
    """Search DuckDuckGo HTML results without an API key or paid service."""

    def search(self, query, limit=5):
        query = (query or "").strip()
        if not query:
            raise ValueError("Enter something to search for.")
        url = "https://html.duckduckgo.com/html/?" + urlencode({"q": query})
        request = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ASTRA-Desktop/0.2"
        })
        try:
            with urlopen(request, timeout=12) as response:
                page = response.read().decode("utf-8", errors="replace")
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"Live search failed: {exc}") from exc

        parser = _DuckDuckGoParser()
        parser.feed(page)
        unique = []
        seen = set()
        for result in parser.results:
            if result.title and result.url.startswith(("http://", "https://")) and result.url not in seen:
                seen.add(result.url)
                unique.append(result)
            if len(unique) >= max(1, min(limit, 8)):
                break
        if not unique:
            raise RuntimeError("The search provider returned no readable results. Try again or open a search page in your browser.")
        return unique
