document.addEventListener('DOMContentLoaded', function() {
    const videoCards = document.querySelectorAll('.video-card');
    const modal = document.getElementById('videoModal');
    const videoPlayer = document.getElementById('videoPlayer');
    const closeBtn = document.querySelector('.close');
    const modalBackBtn = document.getElementById('modalBackBtn');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const errorMessage = document.querySelector('.error-message');
    const retryBtn = document.querySelector('.retry-btn');

    // Show video and modal with smooth transition
    function showVideo(videoUrl) {
        // Reset states
        errorMessage.style.display = 'none';
        loadingSpinner.style.display = 'block';
        videoPlayer.style.opacity = '0';
        
        // Set up video
        videoPlayer.src = videoUrl;
        modal.style.display = 'block';
        requestAnimationFrame(() => {
            modal.style.opacity = '1';
        });

        // Handle video loading
        videoPlayer.addEventListener('loadeddata', function onLoaded() {
            loadingSpinner.style.display = 'none';
            videoPlayer.style.opacity = '1';
            videoPlayer.play();
            videoPlayer.removeEventListener('loadeddata', onLoaded);
        });

        // Handle video errors
        videoPlayer.addEventListener('error', function onError() {
            loadingSpinner.style.display = 'none';
            errorMessage.style.display = 'block';
            console.error('Error loading video:', videoUrl);
            videoPlayer.removeEventListener('error', onError);
        });
    }

    // Close modal with smooth transition
    function closeModal() {
        modal.style.opacity = '0';
        setTimeout(() => {
            modal.style.display = 'none';
            videoPlayer.pause();
            videoPlayer.currentTime = 0;
            videoPlayer.src = '';
            errorMessage.style.display = 'none';
            loadingSpinner.style.display = 'none';
            videoPlayer.style.opacity = '1';
        }, 300);
    }

    // Event Listeners
    videoCards.forEach(card => {
        card.addEventListener('click', function() {
            showVideo(this.dataset.video);
        });
    });

    // Close buttons handlers
    closeBtn.addEventListener('click', closeModal);
    modalBackBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Escape key to close modal
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            closeModal();
        }
    });

    // Video card hover effects
    videoCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Retry button handler
    retryBtn.addEventListener('click', function() {
        showVideo(videoPlayer.src);
    });
});
