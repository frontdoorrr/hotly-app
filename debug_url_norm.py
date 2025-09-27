#!/usr/bin/env python3
"""Debug URL normalization."""

import sys
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def debug_normalize_url(url: str) -> str:
    """Debug version of URL normalization."""
    print(f"Normalizing: {url}")
    parsed = urlparse(url)
    print(f"  Parsed: {parsed}")
    
    # Remove common tracking parameters
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'ref', 'igshid', '_ga', 'source'
    }
    
    query_params = parse_qs(parsed.query)
    filtered_params = {
        k: v for k, v in query_params.items() 
        if k.lower() not in tracking_params
    }
    
    # Rebuild query string
    new_query = urlencode(filtered_params, doseq=True) if filtered_params else ''
    
    # Normalize the URL (convert to lowercase, normalize path)
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.lower().rstrip('/') or '/',  # Convert path to lowercase too!
        parsed.params,
        new_query,
        ''  # Remove fragment
    ))
    
    print(f"  Normalized: {normalized}")
    return normalized


def test_debug():
    """Test URL normalization with debug output."""
    urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://WWW.INSTAGRAM.COM/P/ABC123/",
        "HTTPS://www.instagram.com/p/ABC123"
    ]
    
    for url in urls:
        norm = debug_normalize_url(url)
        print()


if __name__ == "__main__":
    test_debug()