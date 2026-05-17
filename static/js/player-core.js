// Global Shared Audio Pipeline Singleton
window.CyberPlayer = {
    audioEngine: new Audio(),
    isUserDragging: false,
    
    // Central function to update current playing song details
    loadTrack(name, artist, url) {
        this.audioEngine.pause();
        document.dispatchEvent(new CustomEvent('trackWillChange'));
        
        document.getElementById('song-title').innerText = name;
        document.getElementById('artist-name').innerText = artist;
        
        this.audioEngine.src = url;
        this.audioEngine.load();
        
        // Trigger background play execution right away
        this.audioEngine.play()
            .then(() => document.dispatchEvent(new CustomEvent('trackStatusPlaying')))
            .catch(err => console.warn("Autoplay block tracker:", err));
    }
};
