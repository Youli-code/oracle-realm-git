const tsdList = document.getElementById('tsdList');

// Fetch and display TSDs
async function fetchTSDs() {
  const response = await fetch('http://127.0.0.1:5000/articles');
  const articles = await response.json();
  articles
    .filter(article => article.type === 'TSD')
    .forEach(displayArticle);
}

// Display a single article
function displayArticle(article) {
  const articleDiv = document.createElement('div');
  articleDiv.classList.add('card', 'mb-3');
  articleDiv.innerHTML = `
    <div class="card-body">
      <h5 class="card-title">${article.title}</h5>
      <p class="card-text">${article.content}</p>
      <p class="card-text"><small class="text-muted">Tags: ${article.tags.join(', ')}</small></p>
    </div>
  `;
  tsdList.appendChild(articleDiv);
}

// Fetch TSDs when the page loads
fetchTSDs();