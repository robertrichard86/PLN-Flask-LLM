import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    return jsonify({"response": f"Você disse: {message}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render usa variável PORT
    app.run(host="0.0.0.0", port=port)
