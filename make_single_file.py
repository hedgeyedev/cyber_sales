#!/usr/bin/env python3
"""Make one self-contained report HTML for SharePoint: inline Chart.js (no CDN, CSP-safe)
and add a visible "Data as of" banner.

Usage: python3 make_single_file.py IN.html OUT.html "Nov 3, 2026 6:00 AM ET"
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
CDN_TAG = re.compile(r'<script\s+src="https://cdn\.jsdelivr\.net/npm/chart\.js[^"]*"\s*></script>')


def build(src, dst, as_of):
    html = Path(src).read_text()
    chart_js = (HERE / "vendor" / "chart.umd.js").read_text()
    html, n = CDN_TAG.subn(lambda _: "<script>" + chart_js + "</script>", html)
    if n == 0:
        print("note: no Chart.js CDN tag in " + str(src))
    banner = ('<div style="background:#2c5aa0;color:#fff;padding:8px 16px;font:14px sans-serif">'
              f'<strong>Data as of {as_of}</strong> &middot; refreshed automatically; '
              'reload for the latest.</div>')
    html, n = re.subn(r"(<body[^>]*>)", lambda m: m.group(1) + banner, html, count=1)
    if n == 0:
        sys.exit("no <body> tag found")
    Path(dst).write_text(html)
    print(f"wrote {dst} ({len(html)//1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    build(*sys.argv[1:])
