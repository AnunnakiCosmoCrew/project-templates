#!/usr/bin/env python3
"""Stand-in for @axe-core/cli in unit tests: prints canned axe JSON for each URL given.

A page whose URL ends in /bad.html gets two violations (one serious, one minor) plus
one critical; every other page is clean. Mirrors the `axe --stdout` output shape.
"""
import json
import sys

urls = [a for a in sys.argv[1:] if a.startswith("http")]
out = []
for url in urls:
    violations = []
    if url.endswith("/bad.html"):
        violations = [
            {"id": "image-alt", "impact": "critical", "help": "Images must have alternative text",
             "helpUrl": "https://dequeuniversity.com/rules/axe/4.14/image-alt",
             "nodes": [{"target": ["#logo"], "html": "<img id=logo>"}]},
            {"id": "label", "impact": "critical", "help": "Form elements must have labels",
             "helpUrl": "https://dequeuniversity.com/rules/axe/4.14/label",
             "nodes": [{"target": ["#email"], "html": "<input id=email>"}]},
            {"id": "region", "impact": "moderate", "help": "All page content should be contained by landmarks",
             "helpUrl": "https://dequeuniversity.com/rules/axe/4.14/region",
             "nodes": [{"target": ["p"], "html": "<p>"}]},
        ]
    out.append({"url": url, "violations": violations})
json.dump(out, sys.stdout)
