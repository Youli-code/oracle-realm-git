async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    const type = document.getElementById('sourceTypeFilter').value;
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '';

    if (!query) {
        resultsDiv.innerHTML = '<p class="text-muted">Please enter a search term.</p>';
        return;
    }

    let url = `http://127.0.0.1:5000/search?q=${encodeURIComponent(query)}`;
    if (type) url += `&source_type=${type}`;

    try {
        const res = await fetch(url);
        const articles = await res.json();

        if (articles.length === 0) {
            resultsDiv.innerHTML = '<p class="text-muted">No results found.</p>';
            return;
        }

        articles.forEach(article => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            card.innerHTML = `
        <div class="card-body">
          <h5 class="card-title">${article.title}</h5>
          <p class="card-text">${article.content}</p>
          <p class="card-text"><small class="text-muted">Tags: ${article.tags.join(', ')}</small></p>
          <p class="card-text"><small class="text-muted">Type: ${article.type} | Source: ${article.source_type}</small></p>
        </div>
      `;
            resultsDiv.appendChild(card);
        });
    } catch (err) {
        console.error(err);
        resultsDiv.innerHTML = '<p class="text-danger">Error fetching search results.</p>';
    }
}
