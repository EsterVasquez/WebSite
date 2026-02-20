const pendingChatsEl = document.getElementById("pendingChats");
const archivedChatsEl = document.getElementById("archivedChats");
const chatHeaderEl = document.getElementById("chatHeader");
const chatMessagesEl = document.getElementById("chatMessages");
const chatInputEl = document.getElementById("chatInput");
const sendChatForm = document.getElementById("sendChatForm");
const sendChatBtn = document.getElementById("sendChatBtn");
const resolveChatBtn = document.getElementById("resolveChatBtn");
const reopenChatBtn = document.getElementById("reopenChatBtn");
const chatWindowLabel = document.getElementById("chatWindowLabel");
const chatFeedback = document.getElementById("chatFeedback");
const reloadChatsBtn = document.getElementById("reloadChatsBtn");
const threadsPanelEl = document.getElementById("threadsPanel");
const conversationPanelEl = document.getElementById("conversationPanel");
const mobileThreadsBtn = document.getElementById("mobileThreadsBtn");
const mobileConversationBtn = document.getElementById("mobileConversationBtn");
const chatShortcutsEl = document.getElementById("chatShortcuts");
const SEND_BUTTON_DEFAULT = `
    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 11.5L21 3l-8.5 18-2.5-7L3 11.5z"></path>
    </svg>
`;
const SEND_BUTTON_LOADING = `
    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <circle cx="12" cy="12" r="9" stroke-width="2" class="opacity-30"></circle>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 00-9-9"></path>
    </svg>
`;

let chatData = { pending: [], archived: [] };
let activeChat = null;
let chatsSocket = null;
let reconnectTimer = null;
let realtimeRefreshInProgress = false;
let pendingRealtimeUserId = null;
let pollingTimer = null;
let mobileView = "threads";

function isMobileLayout() {
    return window.innerWidth < 1024;
}

function applyMobileToggleButtonStyles() {
    if (!mobileThreadsBtn || !mobileConversationBtn) return;
    const isThreads = mobileView === "threads";
    mobileThreadsBtn.className = `flex-1 px-3 py-2 rounded-lg text-sm font-semibold ${isThreads ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-700"}`;
    mobileConversationBtn.className = `flex-1 px-3 py-2 rounded-lg text-sm font-semibold ${isThreads ? "bg-slate-200 text-slate-700" : "bg-slate-900 text-white"}`;
}

function setMobileView(targetView) {
    mobileView = targetView;
    if (!threadsPanelEl || !conversationPanelEl) return;

    if (!isMobileLayout()) {
        threadsPanelEl.classList.remove("hidden");
        conversationPanelEl.classList.remove("hidden");
        conversationPanelEl.classList.add("flex");
        chatShortcutsEl?.classList.remove("hidden");
        applyMobileToggleButtonStyles();
        return;
    }

    const showThreads = mobileView === "threads";
    threadsPanelEl.classList.toggle("hidden", !showThreads);
    conversationPanelEl.classList.toggle("hidden", showThreads);
    conversationPanelEl.classList.add("flex");
    if (chatShortcutsEl) {
        chatShortcutsEl.classList.toggle("hidden", !showThreads);
    }
    applyMobileToggleButtonStyles();
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Error inesperado.");
    }
    return data;
}

function badge(status) {
    if (status === "pending") return '<span class="text-[11px] bg-orange-100 text-orange-700 px-2 py-0.5 rounded">Pendiente</span>';
    return '<span class="text-[11px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded">Resuelto</span>';
}

function renderThreadsList(container, threads) {
    if (!threads.length) {
        container.innerHTML = '<li class="text-xs text-slate-500">Sin chats en esta sección.</li>';
        return;
    }
    container.innerHTML = threads
        .map((thread) => `
            <li>
                <button
                    class="w-full text-left rounded-xl border p-3 transition ${activeChat && activeChat.user_id === thread.user_id ? "border-cyan-500 bg-cyan-50 shadow-sm" : "border-slate-200 bg-white hover:bg-slate-100 hover:border-slate-300"}"
                    data-chat-user="${thread.user_id}"
                >
                    <div class="flex items-center justify-between gap-2">
                        <p class="font-semibold text-slate-800">${thread.name}</p>
                        ${badge(thread.status)}
                    </div>
                    <p class="text-xs text-slate-500">${thread.phone_number}</p>
                    <p class="text-xs text-slate-600 mt-1">${thread.window_label}</p>
                    <p class="text-xs text-slate-500 mt-1 whitespace-normal break-words">${thread.last_message || "Sin mensajes recientes."}</p>
                </button>
            </li>
        `)
        .join("");

    container.querySelectorAll("[data-chat-user]").forEach((button) => {
        button.addEventListener("click", async (event) => {
            const userId = Number(event.currentTarget.dataset.chatUser);
            const thread = [...chatData.pending, ...chatData.archived].find((item) => item.user_id === userId);
            if (!thread) return;
            activeChat = thread;
            renderAllThreads();
            await loadMessages(userId);
            updateChatHeader(thread);
            setMobileView("conversation");
        });
    });
}

function renderAllThreads() {
    renderThreadsList(pendingChatsEl, chatData.pending);
    renderThreadsList(archivedChatsEl, chatData.archived);
}

function updateChatHeader(thread) {
    chatHeaderEl.querySelector("div:first-child").innerHTML = `
        <p class="font-semibold text-slate-800">${thread.name}</p>
        <p class="text-xs text-slate-500">${thread.phone_number}</p>
    `;
    chatWindowLabel.textContent = thread.window_label;
    if (thread.window_expired) {
        chatWindowLabel.className = "text-xs text-rose-600";
    } else {
        chatWindowLabel.className = "text-xs text-emerald-700";
    }
    resolveChatBtn.classList.toggle("hidden", thread.status !== "pending");
    reopenChatBtn.classList.toggle("hidden", thread.status !== "resolved");
}

function renderMessages(messages) {
    if (!messages.length) {
        chatMessagesEl.innerHTML = '<p class="text-sm text-slate-500">Sin mensajes en este chat.</p>';
        return;
    }
    chatMessagesEl.innerHTML = messages
        .map((message) => {
            const role = message.sender_role === "agent" ? "agent" : message.sender_role === "bot" ? "bot" : "user";
            const isIncoming = role === "user";
            const roleLabel = role === "agent" ? "Agente" : role === "bot" ? "Bot" : "Cliente";
            const bubbleClass =
                role === "agent"
                    ? "bg-emerald-600 text-white"
                    : role === "bot"
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-100 text-slate-800 border border-slate-200";
            return `
                <article class="flex ${isIncoming ? "justify-start" : "justify-end"}">
                    <div class="max-w-[82%] rounded-xl px-3 py-2 ${bubbleClass}">
                        <p class="text-[11px] uppercase tracking-wide opacity-80">${roleLabel}</p>
                        <p class="text-sm whitespace-pre-wrap break-words">${message.content || "(sin contenido)"}</p>
                        <p class="text-[11px] mt-1 opacity-80">${new Date(message.created_at).toLocaleString("es-MX")}</p>
                    </div>
                </article>
            `;
        })
        .join("");
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

async function loadThreads(preferredUserId = null) {
    chatData = await requestJson("/api/dashboard/chats/threads/");
    renderAllThreads();

    let target = null;
    if (preferredUserId) {
        target = [...chatData.pending, ...chatData.archived].find((item) => item.user_id === Number(preferredUserId));
    }
    if (!target && activeChat) {
        target = [...chatData.pending, ...chatData.archived].find((item) => item.user_id === activeChat.user_id);
    }
    if (!target) {
        target = chatData.pending[0] || chatData.archived[0] || null;
    }
    if (!target) {
        activeChat = null;
        chatMessagesEl.innerHTML = '<p class="text-sm text-slate-500">No hay chats para mostrar.</p>';
        chatWindowLabel.textContent = "Ventana gratuita restante: --";
        resolveChatBtn.classList.add("hidden");
        reopenChatBtn.classList.add("hidden");
        setMobileView("threads");
        return;
    }
    activeChat = target;
    renderAllThreads();
    await loadMessages(target.user_id);
    updateChatHeader(target);
    if (isMobileLayout() && !preferredUserId) {
        setMobileView("threads");
    }
}

async function loadMessages(userId) {
    const data = await requestJson(`/api/dashboard/chats/${userId}/messages/`);
    renderMessages(data.messages);
}

async function refreshFromRealtime(preferredUserId = null) {
    if (realtimeRefreshInProgress) {
        pendingRealtimeUserId = preferredUserId || pendingRealtimeUserId;
        return;
    }

    realtimeRefreshInProgress = true;
    try {
        await loadThreads(preferredUserId || activeChat?.user_id || null);
    } catch (error) {
        chatFeedback.textContent = error.message;
    } finally {
        realtimeRefreshInProgress = false;
        if (pendingRealtimeUserId) {
            const queuedUserId = pendingRealtimeUserId;
            pendingRealtimeUserId = null;
            refreshFromRealtime(queuedUserId);
        }
    }
}

function socketUrl() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${window.location.host}/ws/chats/`;
}

function stopPollingFallback() {
    if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
    }
}

function startPollingFallback() {
    if (pollingTimer) return;
    pollingTimer = setInterval(() => {
        refreshFromRealtime(activeChat?.user_id || null);
    }, 4000);
}

function connectRealtimeSocket() {
    if (chatsSocket && (chatsSocket.readyState === WebSocket.OPEN || chatsSocket.readyState === WebSocket.CONNECTING)) {
        return;
    }

    chatsSocket = new WebSocket(socketUrl());

    chatsSocket.onopen = () => {
        stopPollingFallback();
        chatFeedback.textContent = "Conectado en tiempo real.";
    };

    chatsSocket.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data || "{}");
            const userId = Number(payload.user_id || 0);
            refreshFromRealtime(userId || activeChat?.user_id || null);
        } catch (_error) {
            refreshFromRealtime(activeChat?.user_id || null);
        }
    };

    chatsSocket.onclose = () => {
        startPollingFallback();
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
        }
        reconnectTimer = setTimeout(() => connectRealtimeSocket(), 2000);
    };

    chatsSocket.onerror = () => {
        chatsSocket?.close();
    };
}

async function sendMessage() {
    if (!activeChat) throw new Error("Selecciona un chat antes de enviar.");
    const text = chatInputEl.value.trim();
    if (!text) throw new Error("El mensaje no puede estar vacío.");

    sendChatBtn.disabled = true;
    sendChatBtn.innerHTML = SEND_BUTTON_LOADING;
    await requestJson(`/api/dashboard/chats/${activeChat.user_id}/send/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ text }),
    });
    chatInputEl.value = "";
    await loadMessages(activeChat.user_id);
    await loadThreads(activeChat.user_id);
}

async function resolveChat() {
    if (!activeChat) return;
    await requestJson(`/api/dashboard/chats/${activeChat.user_id}/resolve/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
    });
    chatFeedback.textContent = "Chat marcado como resuelto y movido a archivados.";
    await loadThreads(activeChat.user_id);
}

async function reopenChat() {
    if (!activeChat) return;
    await requestJson(`/api/dashboard/chats/${activeChat.user_id}/reopen/`, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
    });
    chatFeedback.textContent = "Chat reabierto y movido a pendientes.";
    await loadThreads(activeChat.user_id);
}

sendChatForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await sendMessage();
        chatFeedback.textContent = "Mensaje enviado correctamente.";
    } catch (error) {
        chatFeedback.textContent = error.message;
    } finally {
        sendChatBtn.disabled = false;
        sendChatBtn.innerHTML = SEND_BUTTON_DEFAULT;
    }
});

chatInputEl?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || event.shiftKey) return;
    event.preventDefault();
    if (!sendChatForm) return;
    if (typeof sendChatForm.requestSubmit === "function") {
        sendChatForm.requestSubmit();
        return;
    }
    sendChatForm.dispatchEvent(new Event("submit", { cancelable: true }));
});

resolveChatBtn?.addEventListener("click", async () => {
    try {
        await resolveChat();
    } catch (error) {
        chatFeedback.textContent = error.message;
    }
});

reopenChatBtn?.addEventListener("click", async () => {
    try {
        await reopenChat();
    } catch (error) {
        chatFeedback.textContent = error.message;
    }
});

reloadChatsBtn?.addEventListener("click", async () => {
    try {
        await loadThreads(activeChat?.user_id || null);
        chatFeedback.textContent = "Chats actualizados.";
    } catch (error) {
        chatFeedback.textContent = error.message;
    }
});

mobileThreadsBtn?.addEventListener("click", () => {
    setMobileView("threads");
});

mobileConversationBtn?.addEventListener("click", () => {
    if (!activeChat) {
        chatFeedback.textContent = "Selecciona una conversación primero.";
        return;
    }
    setMobileView("conversation");
});

document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    const userId = params.get("user");
    try {
        setMobileView("threads");
        await loadThreads(userId ? Number(userId) : null);
        if (userId) {
            setMobileView("conversation");
        }
        if ("WebSocket" in window) {
            connectRealtimeSocket();
        } else {
            startPollingFallback();
            chatFeedback.textContent = "WebSocket no disponible en este navegador. Se usa actualización automática.";
        }
    } catch (error) {
        chatFeedback.textContent = error.message;
    }
});

window.addEventListener("resize", () => {
    setMobileView(mobileView);
});
