from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import time

# Opções de backend LLM: 'hf_api' ou 'local'
LLM_BACKEND = os.getenv("LLM_BACKEND", "hf_api")  # default hf_api

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET", "troque_esta_chave_para_prod")

# ----- 1) Conector para HF Inference API -----
import requests

HF_API_URL = "https://api-inference.huggingface.co/models/"
HF_MODEL = os.getenv("HF_MODEL", "gpt2")  # trocar para modelo preferido
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", None)

def call_hf_inference(prompt, max_tokens=200):
    if HF_API_KEY is None:
        return {"error": "HUGGINGFACE_API_KEY não está definida."}
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": max_tokens, "temperature": 0.7},
        "options": {"wait_for_model": True}
    }
    resp = requests.post(HF_API_URL + HF_MODEL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        return {"error": f"HF API status {resp.status_code}: {resp.text}"}
    data = resp.json()
    # retorno normalmente: [{"generated_text": "..."}] ou texto direto dependendo do modelo
    if isinstance(data, list) and "generated_text" in data[0]:
        return {"text": data[0]["generated_text"]}
    if isinstance(data, dict) and "error" in data:
        return {"error": data["error"]}
    # fallback se veio texto cru
    return {"text": data if isinstance(data, str) else str(data)}

# ----- 2) Conector local com transformers (carrega modelo localmente) -----
local_generator = None
def ensure_local_model():
    global local_generator
    if local_generator is None:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        model_name = os.getenv("LOCAL_MODEL", "gpt2")  # cuidado com tamanho
        # carga do pipeline
        local_generator = pipeline("text-generation", model=model_name, device=0 if torch.cuda.is_available() else -1)
    return local_generator

def call_local_model(prompt, max_tokens=150):
    try:
        gen = ensure_local_model()
        outputs = gen(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.7, num_return_sequences=1)
        return {"text": outputs[0]["generated_text"]}
    except Exception as e:
        return {"error": str(e)}

# ----- Rotas -----
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    # inicializa histórico na sessão
    if "history" not in session:
        session["history"] = []

    # adiciona usuário ao histórico (memória simples)
    session["history"].append({"role": "user", "text": message, "time": time.time()})

    # constrói prompt simples a partir do histórico (pode ser melhorado)
    # Exemplo básico: concatena últimas N trocas
    hist = session["history"][-6:]  # últimos 6 itens
    prompt = ""
    for turn in hist:
        role = "Usuário" if turn["role"] == "user" else "Assistente"
        prompt += f"{role}: {turn['text']}\n"
    prompt += "Assistente:"

    # chama o backend escolhido
    if LLM_BACKEND == "local":
        resp = call_local_model(prompt, max_tokens=200)
    else:
        resp = call_hf_inference(prompt, max_tokens=200)

    if "error" in resp:
        return jsonify({"error": resp["error"]}), 500

    assistant_text = resp["text"]
    # opcional: limpar prefixos repetidos (se aparecerem)
    if assistant_text.startswith(prompt):
        assistant_text = assistant_text[len(prompt):].strip()

    # salva resposta
    session["history"].append({"role": "assistant", "text": assistant_text, "time": time.time()})
    session.modified = True

    return jsonify({"reply": assistant_text, "history": session["history"]})

@app.route("/reset_history", methods=["POST"])
def reset_history():
    session.pop("history", None)
    return jsonify({"ok": True})

if __name__ == "__main__":
    # debug só local
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
