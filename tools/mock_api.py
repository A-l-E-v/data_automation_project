"""
Простой mock JSON API для локального тестирования.
Эндпоинты:
  GET /get
  GET /json
  GET /sales            -> {"data": [ {order_id, customer_id, order_date, amount}, ... ]}
  POST /post            -> эхо
Логирует каждое обращение.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta, timezone
import random

HOST = "127.0.0.1"
PORT = 5000

def pretty(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

def _gen_sales(n=150):
    now = datetime.now(timezone.utc)
    out = []
    for i in range(1, n + 1):
        days = random.randint(0, 180)
        date = (now - timedelta(days=days)).date().isoformat()
        out.append({
            "order_id": 10_000 + i,
            "customer_id": random.randint(1, 200),
            "order_date": date,
            "amount": round(random.expovariate(1/60) + random.random()*15, 2),
        })
    return out

class SimpleJSONHandler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _log_request(self, body: bytes | None = None):
        now = datetime.now(timezone.utc).isoformat()
        client = f"{self.client_address[0]}:{self.client_address[1]}" if self.client_address else "-"
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        headers = {k: v for k, v in self.headers.items()}

        print(f"\n[{now}] MockAPI request from {client}")
        print(f"  {self.command} {parsed.path} {self.request_version}")
        print(f"  Query params: {pretty(qs)}")
        print(f"  Headers: {pretty(headers)}")
        if body:
            try:
                txt = body.decode("utf-8")
                try:
                    j = json.loads(txt)
                    print(f"  Body (json): {pretty(j)}")
                except Exception:
                    print(f"  Body (text): {txt[:1000]}")
            except Exception:
                print("  Body: (binary)")
        print("-" * 60, flush=True)

    def do_GET(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else None
        self._log_request(body)

        parsed = urlparse(self.path)
        if parsed.path == "/get":
            qs = parse_qs(parsed.query)
            self._send_json({"args": {k: v for k, v in qs.items()}, "message": "ok"})
        elif parsed.path == "/json":
            self._send_json({"slideshow": {"title": "Demo", "slides": [{"title":"s1"}]}})
        elif parsed.path == "/sales":
            self._send_json({"data": _gen_sales(200)})
        else:
            self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        self._log_request(body)

        parsed = urlparse(self.path)
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {"raw": body.decode("utf-8", errors="replace")}

        if parsed.path == "/post":
            self._send_json({"received": payload, "message": "posted"})
        else:
            self._send_json({"error": "not found"}, code=404)

    def log_message(self, format, *args):
        return

def run():
    server = HTTPServer((HOST, PORT), SimpleJSONHandler)
    print(f"Mock API running at http://{HOST}:{PORT} (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("Mock API stopped.")

if __name__ == "__main__":
    run()
