document.addEventListener("DOMContentLoaded", async () => {
  const container = document.querySelector(".section");

  try {
    const res = await fetch("http://127.0.0.1:5000/articles");
    const articles = await res.json();

    const kbds = articles.filter(a => a.type.toUpperCase() === "KBD");

    if (kbds.length === 0) {
      container.innerHTML += '<p style="color: #ffffff;">No KBD articles found.</p>';
    } else {
      kbds.forEach(article => {
        const card = document.createElement("div");
        card.className = "card mb-3 p-3";
        card.innerHTML = `
          <h4><a class="article-link" href="view.html?id=${article.id}&type=KBD" target="_blank">${article.title}</a></h4>
          <p class="article-preview">${article.content.slice(0, 100)}...</p>
        `;
        container.appendChild(card);
      });
    }
  } catch (error) {
    console.error("Error loading KBD articles:", error);
    container.innerHTML += '<p style="color: #ff4d4d;">Failed to load articles.</p>';
  }
});
