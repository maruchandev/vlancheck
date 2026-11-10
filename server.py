#!/usr/bin/env python3
import json, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ===== 事前定義(ここだけ編集する) =====
ROOMS = [
    # 1F
    "N101", "S101", "main",
    # 2F
    "N201", "N202", "N203", "N204", "S201-1", "S201-2",
    "S205", "S206", "S207", "sub",
    # 3F
    "N302", "N303", "S301", "S302", "S304", "S305",
    # 4F
    "N406A", "N406B",
]
PEOPLE = {                                                    # 固定IP → 名前
    "10.0.0.11": "m1",
    "10.0.0.12": "m2",
    "10.0.0.13": "m3",
    "10.0.0.14": "m4",
    "10.0.0.15": "m5",
    "10.0.0.16": "m6",
    "10.0.0.17": "m7",
    "10.0.0.18": "m8",
    "10.0.0.19": "m9",
    "10.0.0.20": "m10",
}
# =====================================

DB = "checklist.json"
LOCK = threading.Lock()          # 同時リクエスト時のファイル更新を排他

def load():
    try:
        with open(DB, encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        d = {}
    for r in ROOMS:                       # 事前定義を反映(追記のみ)
        d.setdefault(r, {"done": False, "time": None, "who": None})
    return d

def save(d):
    with open(DB, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=2)

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    HELP = """VLAN検査ツール 使い方:
  curl 10.0.0.1/p/部屋番号   検査(現場で打つやつ) 例: curl 10.0.0.1/p/N101
  curl 10.0.0.1/a/部屋番号   部屋を追加           例: curl 10.0.0.1/a/N500
  curl 10.0.0.1/d/部屋番号   検査を取り消し      例: curl 10.0.0.1/d/N101
  curl 10.0.0.1/r           一覧(検査済み/未検査・担当者)
  curl 10.0.0.1/t           未完了の部屋だけ表示
  curl 10.0.0.1/g           進捗(件数・%)
  curl 10.0.0.1/h           このヘルプ"""

    def do_GET(self):
        p = self.path.rstrip("/").split("/")[1:]
        if p == [] or p == ["h"]:
            body = self.HELP.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        with LOCK:                              # 読込→更新→保存まで排他
            d = load()
            if p == ["r"]:                       # 一覧
                self._send(200, d)
            elif p == ["t"]:                     # 未完了だけ表示
                self._send(200, {r: v for r, v in d.items() if not v["done"]})
            elif p == ["g"]:                     # 進捗
                done = sum(1 for r in d.values() if r["done"])
                self._send(200, {"total": len(d), "done": done,
                                 "remaining": len(d) - done,
                                 "percent": round(done / len(d) * 100) if d else 0})
            elif len(p) == 2 and p[0] == "a":      # 追加(リストにない部屋)
                if p[1] in d:
                    self._send(200, {"ok": f"{p[1]} 登録済み"})
                else:
                    d[p[1]] = {"done": False, "time": None, "who": None}
                    save(d)
                    self._send(200, {"ok": f"追加 {p[1]}", "total": len(d)})
            elif len(p) == 2 and p[0] == "p":      # 検査 → 誰がやったか記録
                if p[1] not in d:
                    self._send(404, {"error": f"未登録: {p[1]}"})
                else:
                    who = PEOPLE.get(self.client_address[0], self.client_address[0])
                    d[p[1]] = {"done": True,
                               "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                               "who": who}
                    save(d)
                    self._send(200, {"ok": f"{p[1]} 検査済み by {who}"})
            elif len(p) == 2 and p[0] == "d":      # 取り消し
                if p[1] in d:
                    d[p[1]] = {"done": False, "time": None, "who": None}
                    save(d)
                    self._send(200, {"ok": f"{p[1]} 未検査に戻した"})
                else:
                    self._send(404, {"error": f"未登録: {p[1]}"})
            else:
                self.send_error(404)

print("listening :80")
ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
