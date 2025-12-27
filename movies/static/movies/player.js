class JetflixPlayer {
    constructor() {
        this.video = document.getElementById('videoPlayer');
        this.container = document.getElementById('playerContainer');
        this.controls = document.getElementById('controlsContainer');
        this.centerPlayBtn = document.getElementById('centerPlayBtn');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.bufferingIndicator = document.getElementById('bufferingIndicator');
        this.shortcutsHelp = document.getElementById('shortcutsHelp');
        this.exitButton = document.getElementById('exitButton');
        this.backButton = document.getElementById('backButton');
        
        // Control elements
        this.playPauseBtn = document.getElementById('playPauseBtn');
        this.rewindBtn = document.getElementById('rewindBtn');
        this.forwardBtn = document.getElementById('forwardBtn');
        this.muteBtn = document.getElementById('muteBtn');
        this.volumeSlider = document.getElementById('volumeSlider');
        this.progressBar = document.getElementById('progressBar');
        this.progressFilled = document.getElementById('progressFilled');
        this.progressHandle = document.getElementById('progressHandle');
        this.timeTooltip = document.getElementById('timeTooltip');
        this.currentTimeEl = document.getElementById('currentTime');
        this.durationEl = document.getElementById('duration');
        this.subtitlesBtn = document.getElementById('subtitlesBtn');
        this.qualityBtn = document.getElementById('qualityBtn');
        this.qualityMenu = document.getElementById('qualityMenu');
        this.theaterBtn = document.getElementById('theaterBtn');
        this.fullscreenBtn = document.getElementById('fullscreenBtn');
        
        // State
        this.isPlaying = false;
        this.isMuted = false;
        this.isFullscreen = false;
        this.isTheaterMode = false;
        this.subtitlesEnabled = false;
        this.currentQuality = '1080';
        this.controlsTimeout = null;
        this.lastVolume = 1;
        this.isDragging = false;
        
        // User preferences (session storage)
        this.loadPreferences();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.setupProgressBar();
        this.setupVolumeControl();
        this.setupQualityMenu();
        this.hideLoadingIndicator();
        this.showCenterPlayButton();
    }
    
    setupEventListeners() {
        // Video events
        this.video.addEventListener('loadstart', () => this.showLoadingIndicator());
        this.video.addEventListener('canplay', () => this.hideLoadingIndicator());
        this.video.addEventListener('waiting', () => this.showBufferingIndicator());
        this.video.addEventListener('playing', () => this.hideBufferingIndicator());
        this.video.addEventListener('play', () => this.onPlay());
        this.video.addEventListener('pause', () => this.onPause());
        this.video.addEventListener('timeupdate', () => this.updateProgress());
        this.video.addEventListener('loadedmetadata', () => this.updateDuration());
        this.video.addEventListener('volumechange', () => this.updateVolumeUI());
        this.video.addEventListener('ended', () => this.onVideoEnd());
        
        // Control events - ensure elements exist before adding listeners
        if (this.playPauseBtn) this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
        if (this.centerPlayBtn) this.centerPlayBtn.addEventListener('click', () => this.togglePlayPause());
        if (this.rewindBtn) this.rewindBtn.addEventListener('click', () => this.rewind());
        if (this.forwardBtn) this.forwardBtn.addEventListener('click', () => this.forward());
        if (this.muteBtn) this.muteBtn.addEventListener('click', () => this.toggleMute());
        if (this.subtitlesBtn) this.subtitlesBtn.addEventListener('click', () => this.toggleSubtitles());
        if (this.qualityBtn) this.qualityBtn.addEventListener('click', () => this.toggleQualityMenu());
        if (this.theaterBtn) this.theaterBtn.addEventListener('click', () => this.toggleTheaterMode());
        if (this.fullscreenBtn) this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        
        // Container events
        this.container.addEventListener('mousemove', () => this.showControls());
        this.container.addEventListener('mouseleave', () => this.hideControls());
        this.container.addEventListener('click', (e) => {
            if (e.target === this.container || e.target === this.video) {
                this.togglePlayPause();
            }
        });
        
        // Fullscreen events
        document.addEventListener('fullscreenchange', () => this.onFullscreenChange());
        document.addEventListener('webkitfullscreenchange', () => this.onFullscreenChange());
        document.addEventListener('mozfullscreenchange', () => this.onFullscreenChange());
        document.addEventListener('MSFullscreenChange', () => this.onFullscreenChange());
        
        // Quality menu outside click
        document.addEventListener('click', (e) => {
            if (this.qualityBtn && this.qualityMenu && 
                !this.qualityBtn.contains(e.target) && !this.qualityMenu.contains(e.target)) {
                this.hideQualityMenu();
            }
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Prevent default for our shortcuts
            const shortcuts = [' ', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'KeyM', 'KeyF', 'KeyS', 'KeyQ', 'Escape'];
            if (shortcuts.includes(e.code)) {
                e.preventDefault();
            }
            
            switch (e.code) {
                case 'Space':
                    this.togglePlayPause();
                    break;
                case 'ArrowLeft':
                    this.rewind();
                    break;
                case 'ArrowRight':
                    this.forward();
                    break;
                case 'ArrowUp':
                    this.volumeUp();
                    break;
                case 'ArrowDown':
                    this.volumeDown();
                    break;
                case 'KeyM':
                    this.toggleMute();
                    break;
                case 'KeyF':
                    this.toggleFullscreen();
                    break;
                case 'KeyS':
                    this.toggleSubtitles();
                    break;
                case 'KeyQ':
                    this.cycleQuality();
                    break;
                case 'Escape':
                    this.exitPlayer();
                    break;
                case 'Slash':
                    if (e.shiftKey) { // ? key
                        this.toggleShortcutsHelp();
                    }
                    break;
            }
        });
    }
    
    setupProgressBar() {
        this.progressBar.addEventListener('click', (e) => this.seekToPosition(e));
        this.progressBar.addEventListener('mousemove', (e) => this.showTimeTooltip(e));
        this.progressBar.addEventListener('mouseleave', () => this.hideTimeTooltip());
        
        // Drag functionality
        this.progressHandle.addEventListener('mousedown', (e) => this.startDragging(e));
        document.addEventListener('mousemove', (e) => this.onDrag(e));
        document.addEventListener('mouseup', () => this.stopDragging());
    }
    
    setupVolumeControl() {
        this.volumeSlider.addEventListener('input', (e) => {
            const volume = e.target.value / 100;
            this.setVolume(volume);
        });
        
        // Set initial volume from preferences
        this.setVolume(this.lastVolume);
        this.volumeSlider.value = this.lastVolume * 100;
    }
    
    setupQualityMenu() {
        const qualityOptions = this.qualityMenu.querySelectorAll('.quality-option');
        qualityOptions.forEach(option => {
            option.addEventListener('click', () => {
                const quality = option.dataset.quality;
                this.setQuality(quality);
                this.hideQualityMenu();
            });
        });
    }
    
    // Playback controls
    togglePlayPause() {
        if (this.video.paused) {
            this.play();
        } else {
            this.pause();
        }
    }
    
    play() {
        const playPromise = this.video.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.error('Error playing video:', error);
            });
        }
    }
    
    pause() {
        this.video.pause();
    }
    
    rewind() {
        const newTime = Math.max(0, this.video.currentTime - 5);
        console.log(`Rewind: ${this.video.currentTime} -> ${newTime}`);
        this.video.currentTime = newTime;
        this.showControls();
    }
    
    forward() {
        // Wait for video metadata to be loaded
        if (!this.video.duration || isNaN(this.video.duration) || this.video.duration === 0) {
            console.log('Video duration not available yet');
            return;
        }
        
        const currentTime = this.video.currentTime || 0;
        const duration = this.video.duration;
        const newTime = Math.min(duration - 0.1, currentTime + 5); // Leave 0.1s buffer from end
        
        console.log(`Forward: ${currentTime.toFixed(2)} -> ${newTime.toFixed(2)} (duration: ${duration.toFixed(2)})`);
        
        try {
            this.video.currentTime = newTime;
        } catch (error) {
            console.error('Error setting video time:', error);
        }
        
        this.showControls();
    }
    
    // Volume controls
    toggleMute() {
        if (this.isMuted) {
            this.unmute();
        } else {
            this.mute();
        }
    }
    
    mute() {
        this.lastVolume = this.video.volume;
        this.video.volume = 0;
        this.isMuted = true;
        this.savePreferences();
    }
    
    unmute() {
        this.video.volume = this.lastVolume;
        this.isMuted = false;
        this.savePreferences();
    }
    
    setVolume(volume) {
        this.video.volume = Math.max(0, Math.min(1, volume));
        if (volume > 0) {
            this.lastVolume = volume;
            this.isMuted = false;
        }
        this.savePreferences();
    }
    
    volumeUp() {
        const newVolume = Math.min(1, this.video.volume + 0.1);
        this.setVolume(newVolume);
        this.volumeSlider.value = newVolume * 100;
        this.showControls();
    }
    
    volumeDown() {
        const newVolume = Math.max(0, this.video.volume - 0.1);
        this.setVolume(newVolume);
        this.volumeSlider.value = newVolume * 100;
        this.showControls();
    }
    
    // Progress bar functionality
    seekToPosition(e) {
        const rect = this.progressBar.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        this.video.currentTime = pos * this.video.duration;
    }
    
    startDragging(e) {
        this.isDragging = true;
        this.container.classList.add('dragging');
        e.preventDefault();
    }
    
    onDrag(e) {
        if (!this.isDragging) return;
        
        const rect = this.progressBar.getBoundingClientRect();
        const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        this.video.currentTime = pos * this.video.duration;
    }
    
    stopDragging() {
        this.isDragging = false;
        this.container.classList.remove('dragging');
    }
    
    showTimeTooltip(e) {
        const rect = this.progressBar.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        const time = pos * this.video.duration;
        
        this.timeTooltip.textContent = this.formatTime(time);
        this.timeTooltip.style.left = `${e.clientX - rect.left}px`;
        this.timeTooltip.classList.add('show');
    }
    
    hideTimeTooltip() {
        this.timeTooltip.classList.remove('show');
    }
    
    // Quality controls
    toggleQualityMenu() {
        this.qualityMenu.classList.toggle('show');
    }
    
    hideQualityMenu() {
        this.qualityMenu.classList.remove('show');
    }
    
    setQuality(quality) {
        const currentTime = this.video.currentTime;
        const wasPlaying = !this.video.paused;
        
        // Update active quality option
        this.qualityMenu.querySelectorAll('.quality-option').forEach(option => {
            option.classList.toggle('active', option.dataset.quality === quality);
        });
        
        // Update quality text
        const qualityText = this.qualityBtn.querySelector('.quality-text');
        switch (quality) {
            case '480':
                qualityText.textContent = 'SD';
                break;
            case '720':
                qualityText.textContent = 'HD';
                break;
            case '1080':
                qualityText.textContent = 'FHD';
                break;
        }
        
        this.currentQuality = quality;
        
        // In a real implementation, you would switch video sources here
        // For now, we'll just simulate the quality change
        if (wasPlaying) {
            this.video.currentTime = currentTime;
            this.play();
        }
        
        this.savePreferences();
    }
    
    cycleQuality() {
        const qualities = ['480', '720', '1080'];
        const currentIndex = qualities.indexOf(this.currentQuality);
        const nextIndex = (currentIndex + 1) % qualities.length;
        this.setQuality(qualities[nextIndex]);
        this.showControls();
    }
    
    // Subtitle controls
    toggleSubtitles() {
        this.subtitlesEnabled = !this.subtitlesEnabled;
        
        // Toggle subtitle tracks
        const tracks = this.video.textTracks;
        for (let i = 0; i < tracks.length; i++) {
            tracks[i].mode = this.subtitlesEnabled ? 'showing' : 'hidden';
        }
        
        // Update button appearance
        this.subtitlesBtn.style.opacity = this.subtitlesEnabled ? '1' : '0.6';
        
        this.savePreferences();
        this.showControls();
    }
    
    // Display mode controls
    toggleTheaterMode() {
        this.isTheaterMode = !this.isTheaterMode;
        this.container.classList.toggle('theater-mode', this.isTheaterMode);
        this.theaterBtn.style.opacity = this.isTheaterMode ? '1' : '0.6';
        this.showControls();
    }
    
    toggleFullscreen() {
        if (this.isFullscreen) {
            this.exitFullscreen();
        } else {
            this.enterFullscreen();
        }
    }
    
    enterFullscreen() {
        const element = this.container;
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }
    }
    
    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
    
    // UI updates
    onPlay() {
        this.isPlaying = true;
        this.playPauseBtn.querySelector('.play-icon').style.display = 'none';
        this.playPauseBtn.querySelector('.pause-icon').style.display = 'block';
        this.hideCenterPlayButton();
    }
    
    onPause() {
        this.isPlaying = false;
        this.playPauseBtn.querySelector('.play-icon').style.display = 'block';
        this.playPauseBtn.querySelector('.pause-icon').style.display = 'none';
        this.showCenterPlayButton();
        this.showControls();
    }
    
    onVideoEnd() {
        this.isPlaying = false;
        this.showCenterPlayButton();
        this.showControls();
    }
    
    onFullscreenChange() {
        this.isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement || 
                              document.mozFullScreenElement || document.msFullscreenElement);
        
        const enterIcon = this.fullscreenBtn.querySelector('.fullscreen-enter');
        const exitIcon = this.fullscreenBtn.querySelector('.fullscreen-exit');
        
        if (this.isFullscreen) {
            enterIcon.style.display = 'none';
            exitIcon.style.display = 'block';
        } else {
            enterIcon.style.display = 'block';
            exitIcon.style.display = 'none';
        }
    }
    
    updateProgress() {
        if (this.isDragging) return;
        
        const progress = (this.video.currentTime / this.video.duration) * 100;
        this.progressFilled.style.width = `${progress}%`;
        this.currentTimeEl.textContent = this.formatTime(this.video.currentTime);
    }
    
    updateDuration() {
        this.durationEl.textContent = this.formatTime(this.video.duration);
    }
    
    updateVolumeUI() {
        const volume = this.video.volume;
        const volumeHigh = this.muteBtn.querySelector('.volume-high');
        const volumeMuted = this.muteBtn.querySelector('.volume-muted');
        
        if (volume === 0 || this.isMuted) {
            volumeHigh.style.display = 'none';
            volumeMuted.style.display = 'block';
        } else {
            volumeHigh.style.display = 'block';
            volumeMuted.style.display = 'none';
        }
        
        this.volumeSlider.value = volume * 100;
    }
    
    // Controls visibility
    showControls() {
        this.controls.classList.add('show');
        this.exitButton.classList.add('show');
        this.backButton.classList.add('show');
        this.container.classList.add('show-cursor');
        
        clearTimeout(this.controlsTimeout);
        this.controlsTimeout = setTimeout(() => {
            if (this.isPlaying && !this.container.matches(':hover')) {
                this.hideControls();
            }
        }, 3000);
    }
    
    hideControls() {
        if (!this.video.paused) {
            this.controls.classList.remove('show');
            this.exitButton.classList.remove('show');
            this.backButton.classList.remove('show');
            this.container.classList.remove('show-cursor');
        }
    }
    
    showCenterPlayButton() {
        this.centerPlayBtn.classList.add('show');
    }
    
    hideCenterPlayButton() {
        this.centerPlayBtn.classList.remove('show');
    }
    
    showLoadingIndicator() {
        this.loadingIndicator.style.display = 'flex';
    }
    
    hideLoadingIndicator() {
        this.loadingIndicator.style.display = 'none';
    }
    
    showBufferingIndicator() {
        this.bufferingIndicator.classList.add('show');
    }
    
    hideBufferingIndicator() {
        this.bufferingIndicator.classList.remove('show');
    }
    
    toggleShortcutsHelp() {
        this.shortcutsHelp.classList.toggle('show');
    }
    
    hideShortcutsHelp() {
        this.shortcutsHelp.classList.remove('show');
    }
    
    // Utility functions
    formatTime(seconds) {
        if (isNaN(seconds)) return '00:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Preferences management
    loadPreferences() {
        const prefs = JSON.parse(sessionStorage.getItem('jetflix-player-prefs') || '{}');
        this.lastVolume = prefs.volume || 1;
        this.subtitlesEnabled = prefs.subtitles || false;
        this.currentQuality = prefs.quality || '1080';
    }
    
    savePreferences() {
        const prefs = {
            volume: this.lastVolume,
            subtitles: this.subtitlesEnabled,
            quality: this.currentQuality
        };
        sessionStorage.setItem('jetflix-player-prefs', JSON.stringify(prefs));
    }
    
    // Navigation functions
    exitPlayer() {
        window.location.href = '/';
    }
    
    goBack() {
        if (document.referrer && document.referrer.includes(window.location.origin)) {
            window.history.back();
        } else {
            window.location.href = '/';
        }
    }
}

// Global functions for template access
function exitPlayer() {
    window.location.href = '/';
}

function goBack() {
    if (document.referrer && document.referrer.includes(window.location.origin)) {
        window.history.back();
    } else {
        window.location.href = '/';
    }
}

// Initialize player when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new JetflixPlayer();
});