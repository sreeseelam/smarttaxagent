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

// Wait for #content to exist before injecting chat HTML
waitForElement('content', (container) => {
  console.log("✅ Found #content — injecting chat widget");

  const chatHTML = `
  <div class="chat-wrapper">
    <div id="chat-container" class="chat-container">
      <div id="starters" class="chat-starters">
        <span class="chat-hint"><b>Try asking:</b></span>
        <button onclick="sendStarter(this)" class="chat-starter-button">Guide me with my tax calculation</button>
        <button onclick="sendStarter(this)" class="chat-starter-button">Provide me Checklist for Tax Optimization</button>
        <button onclick="sendStarter(this)" class="chat-starter-button">Strategies for AGI reduction</button>
        <button onclick="sendStarter(this)" class="chat-starter-button">Tax Planning for Next Year</button>
      </div>

      <!-- ✅ Add scrollable message list -->
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
});

// === Chat Behavior ===

let sessionId = "session_" + Math.random().toString(36).substring(2);

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
      body: JSON.stringify({ session_id: sessionId, message })
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
    // ✅ Smart markdown detection
    const hasMarkdown = /\|.*\|/.test(content) || /\*\*.+\*\*/.test(content) || /[-*] /.test(content);

    if (hasMarkdown) {
      div.innerHTML = marked.parse(content);
    } else {
      // ✅ Normalize line breaks — collapse multiple blank lines
      const normalized = content
        .split('\n')
        .map(line => line.trim())
        .filter((line, index, arr) => {
          const prev = arr[index - 1];
          return !(line === '' && prev === '');
        });

      // ✅ Convert to tight div blocks
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
    if (event.shiftKey) {
      // Allow newline
      return;
    } else {
      // Prevent default (no newline) and send message
      event.preventDefault();
      sendMessage();
    }
  }
}