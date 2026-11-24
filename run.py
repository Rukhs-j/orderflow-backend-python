"""Run from source or the bundled Windows runtime."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import uvicorn

if __name__ == "__main__":
    print("OrderFlow: http://localhost:"+os.getenv("PORT", "8082"))
    uvicorn.run("application:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8082")))
