"""Refresh IMGV in index.html: a content stamp for every image that was replaced after its first publish.

GitHub Pages lets a browser keep an image for 10 minutes without asking again, so a file swapped in place keeps
showing its old pixels. index.html appends ?v=<stamp> to the URLs listed in IMGV, which gives a replaced image a
new URL. Run from the repo root after replacing images and before committing:

    python tools/stamp_images.py
"""
import hashlib, json, os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


commits = {}
for line in git("log", "--format=", "--name-only", "--", "img").splitlines():
    if line:
        commits[line] = commits.get(line, 0) + 1
changed = {line[3:] for line in git("status", "--porcelain", "--", "img").splitlines() if line[:2].strip() == "M"}

stamps = {}
for path in sorted(set(commits) | changed):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        continue
    if commits.get(path, 0) >= 2 or (path in changed and commits.get(path, 0) >= 1):
        stamps[path] = hashlib.md5(open(full, "rb").read()).hexdigest()[:8]

page_path = os.path.join(ROOT, "index.html")
page = open(page_path, encoding="utf-8").read()
m = re.search(r"^const IMGV = (.*);$", page, re.M)
if not m:
    raise SystemExit("index.html has no `const IMGV = {...};` line")
page = page[:m.start(1)] + json.dumps(stamps, separators=(",", ":")) + page[m.end(1):]
open(page_path, "w", encoding="utf-8", newline="\n").write(page)
print("stamped %d replaced images" % len(stamps))
