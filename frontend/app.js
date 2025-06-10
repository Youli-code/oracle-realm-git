function setRealm() {
  const realm = document.getElementById("activeRealm").value;
  localStorage.setItem("oracleRealm", realm);
  alert(`✅ Realm set to: ${realm}`);

  // Automatically close the modal after setting
  const modal = bootstrap.Modal.getInstance(document.getElementById('realmsModal'));
  modal.hide();
}

async function askCopilot() {
  const question = document.getElementById('aiQuestion').value.trim();
  const realm = localStorage.getItem("oracleRealm") || "git";  // default fallback
  const responseBox = document.getElementById('aiAnswer');
  responseBox.innerHTML = '<em style="color: #cccccc;">Summoning the Oracle...</em>';

  if (!question) {
    responseBox.innerHTML = '<div class="alert alert-warning">Please enter a question.</div>';
    return;
  }

  try {
    const res = await fetch('http://localhost:8000/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, realm })
    });

    const data = await res.json();

    if (data.answer) {
      let output = `
        <div class="alert alert-info" style="color: #000000; font-family: 'Segoe UI', sans-serif;">
          ${data.answer.replace(/\n/g, "<br>")}
        </div>
      `;

      if (data.references && data.references.length > 0) {
        output += `<div class="mt-3" style="color: #cccccc; font-family: 'Segoe UI', sans-serif;"><strong>Sources used:</strong><ul>`;
        data.references.forEach(ref => {
          const page = ref.type === "tsd" ? "tsd.html" : "kbd.html";
          output += `<li><a href="${page}?id=${ref.id}" target="_blank" style="color: #00f6ff;"><strong>${ref.title}</strong></a> (${ref.type}) – tags: ${ref.tags.join(", ")}</li>`;
        });
        output += `</ul></div>`;
      }

      responseBox.innerHTML = output;
    } else if (data.error) {
      responseBox.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
    } else {
      responseBox.innerHTML = `<div class="alert alert-secondary">No response received.</div>`;
    }

  } catch (err) {
    console.error("Ask failed:", err);
    responseBox.innerHTML = `<div class="alert alert-danger">Something went wrong. Please try again.</div>`;
  }
}
