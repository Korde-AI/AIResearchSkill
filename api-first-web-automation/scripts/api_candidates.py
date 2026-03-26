#!/usr/bin/env python3
"""Generate likely API/docs URLs and search queries for a target site."""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse


COMMON_PATHS = [
    "/api",
    "/api/docs",
    "/api/v1",
    "/api/v2",
    "/docs",
    "/developers",
    "/developer",
    "/swagger",
    "/swagger-ui",
    "/openapi.json",
    "/redoc",
    "/help",
    "/support",
]


def normalize_base_url(raw_url: str) -> str:
    parsed = urlparse(raw_url if "://" in raw_url else f"https://{raw_url}")
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or parsed.path
    return f"{scheme}://{netloc}".rstrip("/")


def domain_from_url(raw_url: str) -> str:
    parsed = urlparse(raw_url if "://" in raw_url else f"https://{raw_url}")
    return parsed.netloc or parsed.path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate candidate docs/API URLs.")
    parser.add_argument("--url", required=True, help="Base site URL or domain.")
    parser.add_argument("--task", help="Optional task description.")
    args = parser.parse_args()

    base_url = normalize_base_url(args.url)
    domain = domain_from_url(args.url)
    queries = [
        f"site:{domain} API",
        f"site:{domain} developers",
        f"site:{domain} documentation",
    ]
    if args.task:
        queries.extend(
            [
                f"site:{domain} {args.task} API",
                f"site:{domain} {args.task} docs",
                f"site:{domain} {args.task} endpoint",
            ]
        )

    payload = {
        "base_url": base_url,
        "domain": domain,
        "candidate_urls": [f"{base_url}{path}" for path in COMMON_PATHS],
        "search_queries": queries,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
