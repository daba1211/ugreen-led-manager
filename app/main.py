from flask import Flask, jsonify, render_template, request

from app.config_store import load_config, save_config
from app.disk_monitor import DiskMonitor
from app.led_service import get_led_service

app = Flask(__name__)
led_service = get_led_service()

disk_monitor = DiskMonitor(led_service)
disk_monitor.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def api_get_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def api_save_config():
    data = request.get_json(force=True)
    save_config(data)
    return jsonify({"success": True})


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(led_service.status())


@app.route("/api/apply", methods=["POST"])
def api_apply():
    config = load_config()
    result = led_service.apply_config(config)
    return jsonify(result)


@app.route("/api/off", methods=["POST"])
def api_off():
    result = led_service.all_off()
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
