const chatHistory = document.getElementById("chat-history");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");

function scrollToBottom() {
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function addMessage(text, className) {
  const bubble = document.createElement("div");
  bubble.className = `message ${className}`;
  bubble.textContent = text;
  chatHistory.appendChild(bubble);
  scrollToBottom();
}

function showTyping() {
  const wrapper = document.createElement("div");
  wrapper.className = "typing";
  wrapper.id = "typing-indicator";
  wrapper.innerHTML = "<span></span><span></span><span></span>";
  chatHistory.appendChild(wrapper);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

function showAdvertencia(text) {
  const alert = document.createElement("div");
  alert.className = "message bot alerta";
  alert.textContent = text;
  chatHistory.appendChild(alert);
  scrollToBottom();
}

async function sendMessage(text) {
  addMessage(text, "user");
  messageInput.value = "";
  sendBtn.disabled = true;

  showTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!res.ok) {
      throw new Error(`Error del servidor: ${res.status}`);
    }

    const data = await res.json();

    removeTyping();

    if (data.response) {
      addMessage(data.response, "bot");
    }

    if (data.advertencias && data.advertencias.length > 0) {
      data.advertencias.forEach((w) => showAdvertencia(w));
    }
  } catch (err) {
    removeTyping();
    addMessage("Ups, hubo un problema de conexión. ¡Intentalo de nuevo!", "bot");
    console.error("Error en /api/chat:", err);
  } finally {
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (text) sendMessage(text);
});

function sendQuickAction(text) {
  messageInput.value = text;
  chatForm.dispatchEvent(new Event("submit"));
}

function showWelcome() {
  addMessage(
    "¡Hola Soy Ginga, tu asistente de turismo deportivo y recreativo para Mar del Plata. ¿En qué te puedo ayudar hoy?",
    "bot"
  );

  const quickActions = document.getElementById("quick-actions");
  const acciones = [
    { label: "Paseos Familiares", text: "¿Qué actividades tranquilas o paseos familiares recomendás?" },
    { label: "Actividades en la playa", text: "¿Qué deportes o actividades náuticas hay en la playa?" },
    { label: "Actividades más solicitadas", text: "¿Cuáles son las excursiones o tours más solicitados?" },
  ];

  acciones.forEach((a) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "quick-btn";
    btn.textContent = a.label;
    btn.addEventListener("click", () => sendQuickAction(a.text));
    quickActions.appendChild(btn);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  showWelcome();
  messageInput.focus();
});
