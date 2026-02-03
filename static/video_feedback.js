// Video recording functionality
let mediaRecorder;
let recordedChunks = [];
let videoBlob = null;
let stream = null;

document.addEventListener('DOMContentLoaded', function() {
    const startRecord = document.getElementById('startRecord');
    const stopRecord = document.getElementById('stopRecord');
    const retakeVideo = document.getElementById('retakeVideo');
    const videoPreview = document.getElementById('videoPreview');
    const livePreview = document.getElementById('livePreview');
    const recordedVideo = document.getElementById('recordedVideo');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const hasVideoFeedback = document.getElementById('hasVideoFeedback');    startRecord.addEventListener('click', async function() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            
            // Show live preview
            livePreview.srcObject = stream;
            livePreview.style.display = 'block';
            recordingIndicator.style.display = 'flex';
            recordedVideo.style.display = 'none';
            
            mediaRecorder = new MediaRecorder(stream);
            recordedChunks = [];

            mediaRecorder.ondataavailable = function(e) {
                if (e.data.size > 0) {
                    recordedChunks.push(e.data);
                }
            };

            mediaRecorder.onstop = function() {
                videoBlob = new Blob(recordedChunks, { type: 'video/webm' });
                recordedVideo.src = URL.createObjectURL(videoBlob);
                recordedVideo.style.display = 'block';
                livePreview.style.display = 'none';
                recordingIndicator.style.display = 'none';
                videoPreview.style.display = 'block';
                retakeVideo.style.display = 'block';
                startRecord.style.display = 'none';
                hasVideoFeedback.value = 'true';

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            startRecord.style.display = 'none';
            stopRecord.style.display = 'block';
        } catch (err) {
            console.error("Error accessing camera:", err);
            alert("Could not access camera and microphone. Please ensure you have granted permission.");
        }
    });    stopRecord.addEventListener('click', function() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            stopRecord.style.display = 'none';
            
            // Stop all tracks
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            livePreview.srcObject = null;
        }
    });

    retakeVideo.addEventListener('click', function() {
        videoPreview.style.display = 'none';
        retakeVideo.style.display = 'none';
        startRecord.style.display = 'block';
        recordedVideo.style.display = 'none';
        livePreview.style.display = 'none';
        recordingIndicator.style.display = 'none';
        recordedVideo.src = '';
        videoBlob = null;
        hasVideoFeedback.value = 'false';
    });    // Modify form submission to include video
    document.querySelector('form').addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        
        if (videoBlob && hasVideoFeedback.value === 'true') {
            // Add the video blob with a unique name
            const timestamp = new Date().getTime();
            formData.append('video_feedback', videoBlob, `feedback_${timestamp}.webm`);
        }

        try {
            const response = await fetch(this.action, {
                method: 'POST',
                body: formData,
                // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
            });

            if (response.ok) {
                window.location.href = '/';
            } else {
                throw new Error('Server returned error response');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error submitting feedback. Please try again.');
        }
    });
});
