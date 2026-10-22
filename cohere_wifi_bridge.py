#!/usr/bin/env python3
"""Local Wi-Fi bridge for the COHERE ESP32 prototype. Python standard library only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import socket
import time

HTML_FILE = Path(__file__).with_name("COHERE_WiFi_Enabled.html")
HOST = "0.0.0.0"
PORT = 8000
STATE = {"pending": {}, "rounds": [], "total_rounds": 0, "last_event": None, "last_seen": None}


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "YOUR_COMPUTER_IP"
    finally:
        sock.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/state":
            self.send_json(200, STATE)
            return
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            try:
                body = HTML_FILE.read_bytes()
            except OSError:
                self.send_error(500, "COHERE_WiFi_Enabled.html must be beside this Python file")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404, "Not found")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/decision":
            self.send_error(404, "Not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2048:
                raise ValueError("Invalid request length")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            player = data.get("player")
            action = data.get("action")
            if player not in ("A", "B") or action not in ("C", "D"):
                raise ValueError("player must be A/B and action must be C/D")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_json(400, {"ok": False, "error": str(exc)})
            return

        STATE["pending"][player] = action
        STATE["last_event"] = {"player": player, "action": action, "time": time.time()}
        STATE["last_seen"] = time.time()
        if "A" in STATE["pending"] and "B" in STATE["pending"]:
            a, b = STATE["pending"]["A"], STATE["pending"]["B"]
            if a == "C" and b == "C":
                ap, bp = 3, 3
            elif a == "C" and b == "D":
                ap, bp = 0, 5
            elif a == "D" and b == "C":
                ap, bp = 5, 0
            else:
                ap, bp = 1, 1
            STATE["total_rounds"] += 1
            round_result = {
                "round": STATE["total_rounds"],
                "alpha": a, "beta": b,
                "alphaPayoff": ap, "betaPayoff": bp,
                "timestamp": time.time(),
            }
            STATE["rounds"].append(round_result)
            STATE["rounds"] = STATE["rounds"][-100:]
            STATE["pending"] = {}
            print("ROUND {round}: Alpha={alpha}, Beta={beta}, payoff={alphaPayoff}/{betaPayoff}".format(**round_result))
        self.send_json(200, {"ok": True, "pending": STATE["pending"], "rounds_completed": STATE["total_rounds"]})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    ip = local_ip()
    print("\nCOHERE Wi-Fi bridge is running.")
    print("On this computer, open: http://127.0.0.1:%d" % PORT)
    print("On the same Wi-Fi network, computer IP is likely: %s" % ip)
    print("Open the website on your computer at: http://%s:%d" % (ip, PORT))
    print("Use this ESP32 endpoint in the Arduino sketch: http://%s:%d/api/decision" % (ip, PORT))
    print("Press Ctrl+C to stop. If Windows Firewall asks, allow Python on Private networks only.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping COHERE Wi-Fi bridge...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
