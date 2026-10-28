#!/usr/bin/env python3
"""Split an exported Zaika Worlds demo HTML file into a deployable static site.

The export inlines every image and video as a base64 data URI, which makes
one HTML file too big for GitHub (files over 100 MB are hard-blocked).
This script extracts each inlined asset to a real file and rewrites the
references to relative paths. All other bytes of the page are preserved
unchanged, including recipe text, language switching, search, filters,
FAQs, JSON-LD and the video language-switching logic.

Usage:
    python3 tools/split_export.py <exported-html-path> [output-dir]

The exported HTML path is read from the command line argument. The output
directory defaults to the food-blog-repo directory next to this script's
parent when it is run from the repo, and otherwise to ./food-blog-repo.

Rules:
  * Images go to assets/, deduplicated by content hash. The first use of
    identical bytes decides the file name; later uses reuse the same file.
  * Videos (application/octet-stream, MP4) go to videos/. The Beef Nihari
    language keys in the exported data decide the file name:
        "en"    -> videos/beef-nihari-60s-voiced.mp4
        "hi"    -> videos/beef-nihari-60s-voiced-hi.mp4
        "ru"    -> videos/beef-nihari-60s-voiced-roman.mp4
        "video" -> videos/beef-nihari-60s-voiced.mp4 (the legacy English
                   field, byte-identical to the "en" entry)
    Any other video blob falls back to videos/video-<sha256-prefix>.mp4.
  * Only the standard library is used. No file is compressed or re-encoded.
  * The assets/ and videos/ directories are rebuilt on each run so a
    re-run after a future export does not leave stale extracted files.
    Other files in the output directory (vercel.json, README, ...) are
    left untouched.
"""

import base64
import hashlib
import os
import re
import shutil
import sys

DATA_URI_RE = re.compile(
    rb"data:([a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+)(;base64)?,([A-Za-z0-9+/=]+)"
)

EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "video/mp4": "mp4",
    "application/octet-stream": "mp4",  # exported videos use this MIME type
}

VIDEO_NAMES = {
    "en": "beef-nihari-60s-voiced.mp4",
    "hi": "beef-nihari-60s-voiced-hi.mp4",
    "ru": "beef-nihari-60s-voiced-roman.mp4",
    "video": "beef-nihari-60s-voiced.mp4",
}


def slugify(text):
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")[:60] or "asset"


def derive_image_name(data, start, digest, ext, trend_counter):
    """Derive a readable file name from the bytes just before a data URI."""
    tail = data[max(0, start - 800):start].decode("utf-8", errors="replace")
    base = None
    if '"img":' in tail:
        names = re.findall(r'"name":\s*"([^"]+)"', tail)
        if names:
            base = slugify(names[-1])
    if base is None:
        if "hero-photo" in tail:
            base = "hero"
        elif "videoThumbImg" in tail:
            base = "video-thumb"
        elif "modalImg" in tail:
            base = "modal"
        elif "alt-example" in tail:
            base = "alt-example"
        elif "trend-card" in tail:
            base = "trend-card-%d" % trend_counter[0]
            trend_counter[0] += 1
        else:
            base = "asset"
    return "%s-%s.%s" % (base, digest[:8], ext)


def derive_video_name(data, start, digest):
    tail = data[max(0, start - 80):start].decode("utf-8", errors="replace")
    for key in ("\"en\":", "\"hi\":", "\"ru\":", "\"video\":"):
        if key in tail:
            return VIDEO_NAMES[key.strip('":')]
    return "video-%s.mp4" % digest[:8]


def main(argv):
    if len(argv) < 2:
        print("usage: split_export.py <exported-html-path> [output-dir]",
              file=sys.stderr)
        return 2
    input_path = argv[1]
    if len(argv) >= 3:
        out_dir = argv[2]
    else:
        out_dir = os.path.expanduser("~/workspace/food-blog-repo")
    assets_dir = os.path.join(out_dir, "assets")
    videos_dir = os.path.join(out_dir, "videos")

    with open(input_path, "rb") as f:
        data = f.read()

    matches = list(DATA_URI_RE.finditer(data))
    print("found %d data URIs in %s (%d bytes)"
          % (len(matches), input_path, len(data)))

    for subdir in (assets_dir, videos_dir):
        if os.path.isdir(subdir):
            shutil.rmtree(subdir)
        os.makedirs(subdir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    by_hash = {}   # sha256 hex -> relative path (dedupe identical bytes)
    by_target = {}  # target relative path -> sha256 hex (collision guard)
    trend_counter = [1]
    parts = []
    pos = 0
    extracted = []

    for match in matches:
        mime = match.group(1).decode("ascii")
        raw = base64.b64decode(match.group(3))
        digest = hashlib.sha256(raw).hexdigest()
        ext = EXTENSIONS.get(mime)
        if ext is None:
            print("skipping unsupported MIME type %s at offset %d"
                  % (mime, match.start()), file=sys.stderr)
            continue
        if digest in by_hash:
            rel_path = by_hash[digest]
        else:
            if mime == "application/octet-stream":
                filename = derive_video_name(data, match.start(), digest)
                subdir, rel_dir = videos_dir, "videos"
            else:
                filename = derive_image_name(
                    data, match.start(), digest, ext, trend_counter)
                subdir, rel_dir = assets_dir, "assets"
            rel_path = "%s/%s" % (rel_dir, filename)
            if rel_path in by_target and by_target[rel_path] != digest:
                stem, dot, suffix = filename.rpartition(".")
                filename = "%s-%s.%s" % (stem, digest[:8], suffix)
                rel_path = "%s/%s" % (rel_dir, filename)
            target = os.path.join(subdir, filename)
            with open(target, "wb") as out:
                out.write(raw)
            by_hash[digest] = rel_path
            by_target[rel_path] = digest
            extracted.append((rel_path, len(raw), digest))
        parts.append(data[pos:match.start()])
        parts.append(rel_path.encode("ascii"))
        pos = match.end()

    parts.append(data[pos:])
    index_path = os.path.join(out_dir, "index.html")
    with open(index_path, "wb") as out:
        out.write(b"".join(parts))

    print("wrote %s (%d bytes)" % (index_path, os.path.getsize(index_path)))
    print("extracted %d files (%d data URIs, %d deduplicated)"
          % (len(extracted), len(matches), len(matches) - len(extracted)))
    for rel_path, size, digest in extracted:
        print("  %s %d bytes sha256=%s" % (rel_path, size, digest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
