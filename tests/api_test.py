import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.io.loader import call_api
import pandas as pd
import requests
import json


def run_tests():
    print("Call local mock /get (http)...")
    df = call_api("http://127.0.0.1:5000/get", params={"test": "1"}, verify=True)
    print(df.head(), "\n")

    print("Call local mock /json ...")
    df2 = call_api("http://127.0.0.1:5000/json", verify=True)
    print(df2.head(), "\n")

    print(
        "Call local mock /post with JSON body ... (using requests directly to show POST)"
    )
    resp = requests.post("http://127.0.0.1:5000/post", json={"a": 1, "b": "two"})
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text)


if __name__ == "__main__":
    run_tests()
