document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-results-dropdown');

    if (!searchInput || !searchDropdown) return;

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (!query) {
                searchDropdown.classList.add('hidden');
                return;
            }

            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(tracks => {
                    searchDropdown.innerHTML = ''; 
                    
                    if (tracks.length === 0 || tracks.error) {
                        searchDropdown.innerHTML = '<div class="search-result-row"><p class="search-track-name">No tracks found</p></div>';
                        searchDropdown.classList.remove('hidden');
                        return;
                    }

                    tracks.forEach(track => {
                        const row = document.createElement('div');
                        row.className = 'search-result-row';
                        row.innerHTML = `
                            <img class="search-album-thumb" src="${track.album_art || '/static/images/default-cover.jpg'}" alt="Album Art">
                            <div class="search-track-info">
                                <p class="search-track-name">${track.name}</p>
                                <p class="search-track-artist">${track.artist}</p>
                            </div>
                        `;

                        row.addEventListener('click', () => {
                            // Show a temporary loading status on the badge while spotdl is running
                            const statusBadge = document.getElementById('status');
                            if (statusBadge) statusBadge.innerText = "Downloading...";
                            
                            searchDropdown.classList.add('hidden');
                            searchInput.value = '';

                            // Post tracking credentials up to the spotdl wrapper endpoint
                            fetch('/api/download', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    id: track.id,
                                    spotify_url: track.spotify_url
                                })
                            })
                            .then(res => res.json())
                            .then(data => {
                                if (data.error) {
                                    alert("Could not load track from backend scrapers.");
                                    if (statusBadge) statusBadge.innerText = "Error";
                                    return;
                                }
                                // Pass full downloaded track directly into your shared browser player engine core
                                window.CyberPlayer.loadTrack(track.name, track.artist, data.audio_route, track.album_art);
                            })
                            .catch(err => {
                                console.error("Download pipeline error:", err);
                                if (statusBadge) statusBadge.innerText = "Error";
                            });
                        });
                        searchDropdown.appendChild(row);
                    });
                    searchDropdown.classList.remove('hidden');
                })
                .catch(err => console.error("Metadata lookup transaction failed:", err));
        }
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.classList.add('hidden');
        }
    });
});
