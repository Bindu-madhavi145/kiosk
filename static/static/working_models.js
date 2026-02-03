document.addEventListener('DOMContentLoaded', function() {
    const modelCards = document.querySelectorAll('.model-card');
    const videoModal = document.querySelector('.video-modal');
    const modalVideo = document.querySelector('.modal-video');
    const closeModalBtn = document.querySelector('.close-modal');
    let currentVideo = null;

    // Function to play video in modal
    function playVideo(videoSrc) {
        modalVideo.src = videoSrc;
        videoModal.classList.add('active');
        modalVideo.play();
        currentVideo = modalVideo;
    }

    // Function to close modal
    function closeModal() {
        if (currentVideo) {
            currentVideo.pause();
            currentVideo.currentTime = 0;
            currentVideo.src = '';
        }
        videoModal.classList.remove('active');
        currentVideo = null;
    }

    // Add click event to play buttons
    modelCards.forEach(card => {
        const playButton = card.querySelector('.play-button');
        const videoContainer = card.querySelector('.video-container');
        const videoSrc = card.dataset.video;

        playButton.addEventListener('click', (e) => {
            e.preventDefault();
            playVideo(videoSrc);
        });

        videoContainer.addEventListener('click', (e) => {
            if (!e.target.classList.contains('model-video')) {
                playVideo(videoSrc);
            }
        });
    });

    // Close modal when clicking close button
    closeModalBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    videoModal.addEventListener('click', (e) => {
        if (e.target === videoModal) {
            closeModal();
        }
    });

    // Close modal with escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && videoModal.classList.contains('active')) {
            closeModal();
        }
    });
});