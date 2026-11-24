#!/usr/bin/env python3
"""
map_tests.py - Map test IDs from spec Section 9 to actual test functions/files in tb/
"""
import os
import re

TEST_IDS = [
    # Crossbar / AXI4-Lite
    "XB-01", "XB-02", "XB-03", "XB-04", "XB-05", "XB-06", "XB-07", "XB-08",
    "XB-09", "XB-10", "XB-11", "XB-12", "XB-13", "XB-14", "XB-15",
    # APB bridge
    "BR-01", "BR-02", "BR-03", "BR-04", "BR-05", "BR-06",
    # Peripherals
    "UA-01", "UA-02", "UA-03", "UA-04", "UA-05",
    "TM-01", "TM-02", "TM-03",
    "GP-01", "GP-02", "GP-03",
    "CS-01", "CS-02", "CS-03",
    # CDC
    "CD-01", "CD-02", "CD-03", "CD-04", "CD-05"
]

def find_test_locations():
    test_files = []
    for root, dirs, files in os.walk("tb"):
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                test_files.append(os.path.join(root, f))
    
    mapping = {tid: [] for tid in TEST_IDS}
    
    for fpath in test_files:
        with open(fpath) as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            for tid in TEST_IDS:
                # match tid like XB-01 or xb01 or XB01
                num = tid.split("-")[1]
                prefix = tid.split("-")[0]
                pat = rf"\b({prefix}-{num}|{prefix.lower()}{num}|{prefix}{num})\b"
                if re.search(pat, line, re.IGNORECASE):
                    mapping[tid].append((fpath, idx + 1, line.strip()))
                    
    print(f"{'Test ID':<10} | {'Found':<6} | {'Location':<40} | {'Details'}")
    print("-" * 80)
    for tid in TEST_IDS:
        locs = mapping[tid]
        found = "YES" if locs else "NO"
        first_loc = f"{locs[0][0]}:{locs[0][1]}" if locs else "NOT FOUND"
        details = locs[0][2][:30] if locs else ""
        print(f"{tid:<10} | {found:<6} | {first_loc:<40} | {details}")

if __name__ == "__main__":
    find_test_locations()
