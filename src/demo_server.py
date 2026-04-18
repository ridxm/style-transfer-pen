"""Minimal Flask demo UI for penDNA."""
from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

import config
from src import pipeline

app = Flask(__name__)


INDEX_HTML = """<!doctype html>
<title>penDNA</title>
<h1>penDNA</h1>
<p>Draw on the paper with the pen, then enter a prompt and press Go.</p>
<form id="f">
  <label>Capture seconds: <input name="duration" value="15" type="number" min="3" max="120"></label><br>
  <label>Prompt: <input name="prompt" size="60" value="a small house with a tree"></label><br>
  <label><input type="checkbox" name="plot" checked> Plot when done</label><br>
  <button>Go</button>
</form>
<pre id="out"></pre>
<script>
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault();
  const data = new FormData(e.target);
  const body = {
    prompt: data.get('prompt'),
    duration: parseFloat(data.get('duration')),
    plot: data.get('plot') === 'on',
  };
  document.getElementById('out').textContent = 'running...';
  const r = await fetch('/run', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify(body)});
  document.getElementById('out').textContent = JSON.stringify(await r.json(), null, 2);
};
</script>
"""


@app.get("/")
def index():
    return INDEX_HTML


@app.post("/run")
def run():
    body = request.get_json(force=True)
    out = pipeline.run(
        prompt=body.get("prompt", "a simple sketch"),
        duration_s=float(body.get("duration", 15.0)),
        plot=bool(body.get("plot", True)),
    )
    return jsonify({"gcode": str(out)})


@app.get("/outputs/<path:name>")
def outputs(name):
    return send_from_directory(config.OUTPUTS_DIR, name)


def main():
    app.run(host=config.SERVER_HOST, port=config.SERVER_PORT)


if __name__ == "__main__":
    main()
