from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import pytest

if __name__ == "__main__":
    raise SystemExit(pytest.main(["tests", "-q", *sys.argv[1:]]))
