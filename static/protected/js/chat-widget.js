function waitForElement(id, callback, maxAttempts = 20, interval = 100) {
  let attempts = 0;
  const check = () => {
    const el = document.getElementById(id);
    if (el) {
      callback(el);
    } else if (attempts++ < maxAttempts) {
      setTimeout(check, interval);
    } else {
      console.error(`❌ Could not find #${id} after ${maxAttempts} tries.`);
    }
  };
  check();
}

// Get role from URL query string (e.g. ?role=IndividualUser or TaxSpecialist)
const userRole = localStorage.getItem('role') || 'IndividualUser';
console.log("✅ Loaded role from localStorage:", userRole);

const username = localStorage.getItem('username');
const sessionId = `session_${username}_${Date.now()}`;

// Role-specific starter messages
const starterMap = {
  IndividualUser: [
    "Guide me with my Tax calculation",
    "What can I do for max refund?",
    "Missing any deductions to reduce my taxes",
    "List different retiment plans",
    "Provide Tax Optimization Checklist",
    "Provide strategies for AGI reduction",
    "Tax Planning for Next Year"
  ],
  TaxSpecialist: [
    "Help review with tax calculation",
    "List missing deductions/provisions",
    "How to file for Income Tax?",
    "How to file FBAR?",
    "Payment/Refund process",
    "Tax Scenario Comparison"
  ]
};

const selectedStarters = starterMap[userRole] || starterMap.IndividualUser;

const starterButtonsHTML = selectedStarters.map(text =>
  `<button onclick="sendStarter(this)" class="chat-starter-button">${text}</button>`
).join('');

// Wait for #content to exist before injecting chat HTML
waitForElement('content', (container) => {
  console.log(`✅ Found #content — injecting chat widget for role: ${userRole}`);

  const chatHTML = `
    <div class="chat-wrapper">
      <div id="chat-container" class="chat-container">
        <div id="starters" class="chat-starters">
          <span class="chat-hint"><b>Try asking:</b></span>
          ${starterButtonsHTML}
        </div>

        <!-- ✅ Scrollable message list -->
        <div id="message-list" class="chat-messages"></div>
      </div>

      <div id="input-container" class="chat-input-container">
        <textarea id="user-input" rows="1" placeholder="Type your message..." class="chat-textarea" onkeydown="handleEnter(event)"></textarea>
        <button onclick="sendMessage()" class="chat-send-button">Send</button>
        <button onclick="resetChat()" class="chat-reset-button">Reset</button>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', chatHTML);
  startSession();
});

// === Chat Behavior ===

async function startSession() {
  try {
    const res = await fetch('/start-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    const data = await res.json();
    console.log('🧠 Session started:', data);
  } catch (err) {
    console.error("❌ Failed to start session:", err);
  }
}

function sendStarter(button) {
  const input = document.getElementById('user-input');
  input.value = button.textContent;
  sendMessage();
}

async function sendMessage() {
  const input = document.getElementById('user-input');
  const message = input.value.trim();
  if (!message) return;

  appendMessage('user', message);
  const starters = document.getElementById('starters');
  if (starters) starters.style.display = 'none';
  input.value = '';

  // Typing indicator
  appendMessage('assistant', 'Typing...', true);

  try {
    const res = await fetch('/send-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        role: userRole // ✅ Pass role to backend
      })
    });

    const data = await res.json();
    removeTyping();
    appendMessage('assistant', data.response);
  } catch (err) {
    removeTyping();
    appendMessage('assistant', "Something went wrong. Please try again.");
    console.error("❌ Message error:", err);
  }
}

async function resetChat() {
  await fetch('/clear-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  sessionId = "session_" + Math.random().toString(36).substring(2);
  await startSession();
  document.getElementById('chat-container').innerHTML = '';
}

function appendMessage(role, content, isTyping = false) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  if (isTyping) div.id = "typing-indicator";

  if (role === 'assistant') {
    const hasMarkdown = /\|.*\|/.test(content) || /\*\*.+\*\*/.test(content) || /[-*] /.test(content);

    if (hasMarkdown) {
      div.innerHTML = marked.parse(content);
    } else {
      const normalized = content
        .split('\n')
        .map(line => line.trim())
        .filter((line, index, arr) => !(line === '' && arr[index - 1] === ''));

      div.innerHTML = normalized
        .map(line => line ? `<div>${line}</div>` : '<br>')
        .join('');
    }
  } else {
    div.textContent = `You: ${content}`;
  }

  const time = document.createElement('div');
  time.className = "timestamp";
  time.textContent = new Date().toLocaleTimeString();
  div.appendChild(time);

  const container = document.getElementById('message-list');
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const typing = document.getElementById('typing-indicator');
  if (typing) typing.remove();
}

function handleEnter(event) {
  if (event.key === 'Enter') {
    if (event.shiftKey) return;
    event.preventDefault();
    sendMessage();
  }
}