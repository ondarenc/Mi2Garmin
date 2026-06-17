#!/usr/bin/env python3
import csv
import urllib.request
import os
from urllib.parse import urlparse

csv_file = '/home/ondarenc/CascadeProjects/garminport/GPX Mi/20260612_6779095247_MiFitness_hlth_center_sport_track_data.csv'
output_dir = '/home/ondarenc/CascadeProjects/garminport/GPX Mi'

# Read CSV and extract GPX URLs
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Found {len(rows)} GPX URLs to download")

downloaded = []
failed = []

for i, row in enumerate(rows, 1):
    url = row['GPX']
    if not url:
        continue
    
    # Extract filename from URL
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    
    output_path = os.path.join(output_dir, filename)
    
    print(f"[{i}/{len(rows)}] Downloading {filename}...")
    
    try:
        urllib.request.urlretrieve(url, output_path)
        downloaded.append(filename)
        print(f"  ✓ Saved to {output_path}")
    except Exception as e:
        failed.append((filename, str(e)))
        print(f"  ✗ Failed: {e}")

print(f"\n=== Summary ===")
print(f"Downloaded: {len(downloaded)}")
print(f"Failed: {len(failed)}")

if failed:
    print("\nFailed downloads:")
    for filename, error in failed:
        print(f"  - {filename}: {error}")
