#!/usr/bin/env python3
"""
check_image_uniqueness.py
Verifies that all images in assets/ have unique visual representations
using ffmpeg raw 9x8 luma thumbnails and dHash difference comparison.
Prevents duplicate or near-identical transformed images from being published.
"""

import sys
import glob
import subprocess

def get_image_hash(filepath):
    # Run ffmpeg to output 9x8 raw grayscale bytes (72 bytes)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", filepath,
        "-vf", "scale=9:8,format=gray",
        "-f", "rawvideo",
        "-"
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or len(res.stdout) < 72:
        return None
    raw = res.stdout[:72]
    # Compute horizontal difference hash (64 bits)
    h = 0
    for row in range(8):
        for col in range(8):
            p1 = raw[row * 9 + col]
            p2 = raw[row * 9 + col + 1]
            if p1 > p2:
                h |= (1 << (row * 8 + col))
    return h

def hamming_dist(h1, h2):
    return bin(h1 ^ h2).count('1')

def verify_all_assets(threshold=5):
    files = sorted(glob.glob('assets/*.webp'))
    print(f"Scanning {len(files)} asset images using visual dHash...")
    hashes = {}
    for f in files:
        h = get_image_hash(f)
        if h is not None:
            hashes[f] = h

    fpaths = list(hashes.keys())
    duplicates = []
    for i in range(len(fpaths)):
        for j in range(i + 1, len(fpaths)):
            p1, p2 = fpaths[i], fpaths[j]
            dist = hamming_dist(hashes[p1], hashes[p2])
            if dist <= threshold:
                duplicates.append((p1, p2, dist))

    if duplicates:
        print(f"\n[!] WARNING: Found {len(duplicates)} visually near-identical pair(s) (threshold <= {threshold}):")
        for p1, p2, dist in duplicates:
            print(f"  - {p1} <--> {p2} (hamming distance: {dist})")
        return False
    else:
        print(f"\n[OK] All {len(hashes)} images are visually distinct (hamming distance > {threshold}).")
        return True

if __name__ == "__main__":
    thresh = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    ok = verify_all_assets(thresh)
    sys.exit(0 if ok else 1)
