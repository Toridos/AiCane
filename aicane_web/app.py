from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json, subprocess, threading, os

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

ROUTE_FILE = "route_data.json"

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/route", methods=["POST"])
def receive_route():
    """웹에서 경로 JSON 수신 후 cane.py 자동 실행"""
    data = request.get_json()
    with open(ROUTE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n[✅ 새 경로 수신 완료]")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # cane.py 자동 실행 (비동기 스레드)
    threading.Thread(target=run_cane_script).start()

    return jsonify({"status": "received", "route_id": data.get("route_id")})

def run_cane_script():
    """cane.py 실행"""
    try:
        print("[▶️ cane.py 실행 중...]")
        subprocess.run(["python", "cane.py"], check=True)
        print("[🏁 cane.py 실행 완료]")
    except Exception as e:
        print(f"[❌ cane.py 실행 실패]: {e}")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🚀 AiCane Flask 서버 실행 중... http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
