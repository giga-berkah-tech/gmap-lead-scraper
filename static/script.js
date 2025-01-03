document.getElementById('searchButton').addEventListener('click', async () => {
    const searchInput = document.getElementById('searchInput').value.trim();
    const resultsDiv = document.getElementById('results');

    if (!searchInput) {
        resultsDiv.innerHTML = '<p class="text-danger">Please enter a search term.</p>';
        return;
    }

    resultsDiv.innerHTML = '<p class="text-info">Searching...</p>';

    const response = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search: searchInput })
    });

    if (response.ok) {
        const data = await response.json();
        resultsDiv.innerHTML = '<h4>Results:</h4>';
        const list = document.createElement('ul');
        list.className = 'list-group';

        data.data.forEach((business) => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.textContent = business.name || 'Unknown';
            list.appendChild(item);
        });

        resultsDiv.appendChild(list);
    } else {
        const error = await response.json();
        resultsDiv.innerHTML = `<p class="text-danger">${error.error}</p>`;
    }
});
