/**
 * TechMart Support chat frontend.
 *
 * Security note: the JWT is kept in an in-memory variable only (never
 * localStorage/sessionStorage), since localStorage is readable by any
 * script on the page and is a common XSS exfiltration target. The
 * tradeoff: refreshing the page requires signing in again. That's a
 * deliberate choice for a security-conscious capstone, not an oversight.
 */

function stripTrailingSlashes(url) {
  return url.replace(/\/+$/, "");
}

const API_BASE_URL = stripTrailingSlashes(
  (typeof window !== "undefined" && window.TECHMART_CONFIG && window.TECHMART_CONFIG.apiBaseUrl)
    || "http://127.0.0.1:8000"
);
const FALLBACK_PHRASE = "don't have enough information";
const ALL_DOMAINS = ["billing", "technical", "product", "complaint", "faq"];

// ---- Pure helper functions (kept dependency-free so they're unit-testable
// under Node without a browser/DOM) ----------------------------------------

function isFallbackReply(replyText) {
  return typeof replyText === "string" && replyText.includes(FALLBACK_PHRASE);
}

function isValidSessionIdFormat(sessionId) {
  return typeof sessionId === "string" && /^[a-zA-Z0-9-]{1,64}$/.test(sessionId);
}

function sanitizeAgentList(routedAgents) {
  if (!Array.isArray(routedAgents)) return [];
  return routedAgents.filter((a) => ALL_DOMAINS.includes(a));
}

// Export for Node-based unit tests; no-op in the browser.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { isFallbackReply, isValidSessionIdFormat, sanitizeAgentList, stripTrailingSlashes, ALL_DOMAINS };
}

// ---- Browser-only application logic ---------------------------------------

if (typeof window !== "undefined") {
  (function () {
    let authToken = null;
    let currentSessionId = null;

    const loginScreen = document.getElementById("login-screen");
    const appScreen = document.getElementById("app-screen");
    const loginForm = document.getElementById("login-form");
    const loginError = document.getElementById("login-error");
    const logoutBtn = document.getElementById("logout-btn");
    const newChatBtn = document.getElementById("new-chat-btn");
    const sessionIdEl = document.getElementById("session-id");
    const messagesEl = document.getElementById("messages");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const statusItems = document.querySelectorAll(".status-item");

    async function apiFetch(path, options = {}) {
      const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
      if (authToken) headers["Authorization"] = `Bearer ${authToken}`;

      const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
      let body = null;
      try {
        body = await response.json();
      } catch {
        // non-JSON response body; leave as null
      }

      if (!response.ok) {
        const message = (body && (body.error || body.detail)) || `Request failed (${response.status})`;
        throw new Error(typeof message === "string" ? message : JSON.stringify(message));
      }
      return body;
    }

    function showApp() {
      loginScreen.hidden = true;
      appScreen.hidden = false;
      chatInput.focus();
    }

    function showLogin() {
      appScreen.hidden = true;
      loginScreen.hidden = false;
      authToken = null;
      currentSessionId = null;
    }

    function resetConversationUI() {
      currentSessionId = null;
      sessionIdEl.textContent = "—";
      messagesEl.innerHTML = "";
      updateStatusLights([]);
    }

    function updateStatusLights(activeDomains) {
      statusItems.forEach((item) => {
        item.classList.toggle("active", activeDomains.includes(item.dataset.domain));
      });
    }

    function scrollToBottom() {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function renderUserMessage(text) {
      const tpl = document.getElementById("msg-user-template");
      const node = tpl.content.cloneNode(true);
      node.querySelector(".bubble").textContent = text;
      messagesEl.appendChild(node);
      scrollToBottom();
    }

    function renderAssistantMessage(replyText, routedAgents) {
      const tpl = document.getElementById("msg-assistant-template");
      const node = tpl.content.cloneNode(true);
      const wrapper = node.querySelector(".msg-assistant");
      const tagRow = node.querySelector(".tag-row");

      if (isFallbackReply(replyText)) {
        wrapper.classList.add("fallback");
      }

      sanitizeAgentList(routedAgents).forEach((agent) => {
        const tag = document.createElement("span");
        tag.className = "tag";
        tag.innerHTML = `<span class="dot dot-${agent}"></span>${agent}`;
        tagRow.appendChild(tag);
      });

      node.querySelector(".bubble").textContent = replyText;
      messagesEl.appendChild(node);
      scrollToBottom();
    }

    function renderErrorMessage(text) {
      renderAssistantMessage(`⚠ ${text}`, []);
    }

    // ---- Event handlers ----

    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      loginError.hidden = true;

      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value;

      try {
        const result = await apiFetch("/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        authToken = result.data.access_token;
        loginForm.reset();
        showApp();
      } catch (err) {
        loginError.textContent = err.message;
        loginError.hidden = false;
      }
    });

    logoutBtn.addEventListener("click", () => {
      showLogin();
    });

    newChatBtn.addEventListener("click", () => {
      resetConversationUI();
      chatInput.focus();
    });

    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;

      renderUserMessage(message);
      chatInput.value = "";
      chatInput.style.height = "auto";
      sendBtn.disabled = true;

      try {
        const payload = { message };
        if (currentSessionId && isValidSessionIdFormat(currentSessionId)) {
          payload.session_id = currentSessionId;
        }

        const result = await apiFetch("/chat", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        const { reply, routed_agents, session_id } = result.data;
        currentSessionId = session_id;
        sessionIdEl.textContent = session_id.slice(0, 8);

        renderAssistantMessage(reply, routed_agents);
        updateStatusLights(sanitizeAgentList(routed_agents));
      } catch (err) {
        renderErrorMessage(err.message);
      } finally {
        sendBtn.disabled = false;
        chatInput.focus();
      }
    });

    // Auto-grow the textarea, cap handled by CSS max-height
    chatInput.addEventListener("input", () => {
      chatInput.style.height = "auto";
      chatInput.style.height = `${chatInput.scrollHeight}px`;
    });

    // Enter to send, Shift+Enter for newline
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
      }
    });
  })();
}
