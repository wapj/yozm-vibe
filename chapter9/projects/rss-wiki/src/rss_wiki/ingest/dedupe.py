import hashlib
import urllib.parse

TRACKING_PARAM_PREFIXES: tuple[str, ...] = ("utm_",)
TRACKING_PARAM_NAMES: frozenset[str] = frozenset(
    {"fbclid", "gclid", "ref", "ref_src", "mc_cid", "mc_eid"}
)


def normalize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower().rstrip(".")
    fragment = ""
    params = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    filtered = [
        (k, v)
        for k, v in params
        if not any(k.startswith(p) for p in TRACKING_PARAM_PREFIXES)
        and k not in TRACKING_PARAM_NAMES
    ]
    filtered.sort(key=lambda kv: kv[0])
    query = urllib.parse.urlencode(filtered)
    return urllib.parse.urlunsplit((scheme, netloc, parts.path, query, fragment))


def url_hash(url: str) -> str:
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def title_hash(title: str) -> str:
    normalized = title.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
