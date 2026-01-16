class CameraRecognition {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.stream = null;
        this.isRunning = false;
        this.description = document.getElementById('description')?.textContent || '';
        this.messageBox = document.getElementById('faceMessage');
        this.faceDetected = false;
        this.lastSpeechTime = 0;
        this.speechCooldown = 10000; // 10 seconds cooldown between speeches
    }

    async start() {
        try {
            // Get camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });
            
            this.video.srcObject = this.stream;
            await this.video.play();
            
            this.isRunning = true;
            this.startFaceDetection();
            
            // Initialize speech synthesis voices
            this.loadVoices();
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showMessage('Camera access denied or not available', 'error');
        }
    }

    loadVoices() {
        // Load available voices
        if ('speechSynthesis' in window) {
            // Some browsers need this to populate voices
            setTimeout(() => {
                const voices = window.speechSynthesis.getVoices();
                console.log('Available voices:', voices.length);
            }, 1000);
        }
    }

    async startFaceDetection() {
        if (!this.isRunning) return;

        // Set canvas dimensions to match video
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;

        // Face detection loop
        setInterval(() => {
            if (!this.isRunning) return;

            // Draw video frame to canvas
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Get image data for processing
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            // Simulate face detection
            const hasFace = this.simulateFaceDetection(imageData);
            
            if (hasFace && !this.faceDetected) {
                // Face just appeared
                this.faceDetected = true;
                this.showMessage('Face detected!', 'success');
                
                // Speak the description if available
                this.speakDescription();
                
            } else if (!hasFace && this.faceDetected) {
                // Face disappeared
                this.faceDetected = false;
                this.showMessage('Looking for faces...', 'info');
                
            } else if (hasFace && this.faceDetected) {
                // Face still present
                const currentTime = Date.now();
                if (currentTime - this.lastSpeechTime > this.speechCooldown) {
                    // Speak again after cooldown
                    this.speakDescription();
                }
            }
            
        }, 2000); // Check every 2 seconds
    }

    speakDescription() {
        const currentTime = Date.now();
        
        // Check cooldown
        if (currentTime - this.lastSpeechTime < this.speechCooldown) {
            return;
        }
        
        if (this.description && this.description.trim()) {
            // Call global speakText function from camera.html
            if (typeof window.speakText === 'function') {
                window.speakText(this.description);
                this.lastSpeechTime = currentTime;
                this.showMessage('Speaking description...', 'success');
            }
        } else {
            const defaultMessage = "Hello! I recognize you from the uploaded photo.";
            if (typeof window.speakText === 'function') {
                window.speakText(defaultMessage);
                this.lastSpeechTime = currentTime;
            }
        }
    }

    simulateFaceDetection(imageData) {
        // For demo: Simple face detection simulation
        const data = imageData.data;
        let skinPixels = 0;
        
        // Simple skin color detection
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Skin color detection algorithm (simplified)
            if (r > 95 && g > 40 && b > 20 &&
                Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
                Math.abs(r - g) > 15 && r > g && r > b) {
                skinPixels++;
            }
        }
        
        // Calculate percentage of skin pixels
        const totalPixels = imageData.width * imageData.height;
        const skinPercentage = (skinPixels / totalPixels) * 100;
        
        // If more than 2% of pixels look like skin, assume face is present
        // (This is a very simplified simulation)
        return skinPercentage > 2;
        
        // For real implementation, uncomment the line below to always detect face
        // return true; // For testing voice always
    }

    showMessage(message, type = 'info') {
        if (!this.messageBox) return;
        
        this.messageBox.textContent = message;
        this.messageBox.className = 'face-message';
        
        switch(type) {
            case 'success':
                this.messageBox.style.background = 'linear-gradient(45deg, #11998e, #38ef7d)';
                break;
            case 'error':
                this.messageBox.style.background = 'linear-gradient(45deg, #ff416c, #ff4b2b)';
                break;
            default:
                this.messageBox.style.background = 'linear-gradient(45deg, #6a11cb, #2575fc)';
        }
        
        // Add pulse animation
        this.messageBox.classList.add('pulse');
        setTimeout(() => {
            this.messageBox.classList.remove('pulse');
        }, 2000);
    }

    stop() {
        this.isRunning = false;
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.video.srcObject = null;
        }
        
        // Stop any ongoing speech
        if (typeof window.stopSpeaking === 'function') {
            window.stopSpeaking();
        }
    }

    capture() {
        if (!this.isRunning) return;
        
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        return this.canvas.toDataURL('image/jpeg');
    }
}

// Initialize camera when page loads
document.addEventListener('DOMContentLoaded', function() {
    const camera = new CameraRecognition();
    
    // Start camera automatically
    setTimeout(() => {
        camera.start();
    }, 1000);
    
    // Start camera button
    const startBtn = document.getElementById('startCamera');
    if (startBtn) {
        startBtn.addEventListener('click', () => camera.start());
    }
    
    // Stop camera button
    const stopBtn = document.getElementById('stopCamera');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            camera.stop();
            window.location.href = '/upload';
        });
    }
    
    // Close button
    const closeBtn = document.getElementById('closeApp');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            camera.stop();
            window.location.href = '/close';
        });
    }
});