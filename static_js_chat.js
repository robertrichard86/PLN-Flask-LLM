const chatWindow = document.getElementById("chatWindow");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");
const resetBtn = document.getElementById("resetBtn");

function addMessage(role, text){
  const m = document.createElement("div");
  m.className = "msg " + (role === "user" ? "user" : "assistant");
  const b = document.createElement("div");
  b.className = "bubble";
  b.innerText = text;
  m.appendChild(b);
  chatWindow.appendChild(m);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

sendBtn.onclick = async () => {
  const text = msgInput.value.trim();
  if(!text) return;
  addMessage("user", text);
  msgInput.value = "";
  sendBtn.disabled = true;
  sendBtn.innerText = "Enviando...";
  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await resp.json();
    if(resp.ok && data.reply){
      addMessage("assistant", data.reply);
    } else {
      addMessage("assistant", "Erro: " + (data.error || "Resposta inválida"));
    }
  } catch(e){
    addMessage("assistant", "Erro de conexão: " + e.message);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerText = "Enviar";
  }
};

resetBtn.onclick = async () => {
  await fetch("/reset_history", {method: "POST"});
  chatWindow.innerHTML = "";
  addMessage("assistant", "Histórico resetado.");
};
