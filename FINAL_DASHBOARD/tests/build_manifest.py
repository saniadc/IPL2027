"""Write data/MANIFEST.csv: SHA-256 and size of every file in data/ and assets/.

Run after replacing any research file:   python tests/build_manifest.py
The test suite checks the manifest, so an unexpected change to a data file is caught."""
import csv
import hashlib
from pathlib import Path

DASH = Path(__file__).resolve().parents[1]
ROWS = []
for base in (DASH / "data", DASH / "assets"):
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.csv":
            ROWS.append({"file": p.relative_to(DASH).as_posix(),
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                         "bytes": p.stat().st_size})

out = DASH / "data" / "MANIFEST.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["file", "sha256", "bytes"])
    w.writeheader()
    w.writerows(ROWS)
print(f"wrote {out.relative_to(DASH)} with {len(ROWS)} files")
