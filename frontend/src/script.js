// Global variables
let currentStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let currentAuthType = null;

// User data storage (in production, this would be a secure database)
let users = [];
let currentUser = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Biometric Authentication System Loaded');
    
    // Form submission handlers
    document.getElementById('loginForm').addEventListener('submit', handlePasswordLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegistration);
    
    // Audio recording handlers
    document.getElementById('recordBtn').addEventListener('click', startVoiceRecording);
    document.getElementById('stopBtn').addEventListener('click', stopVoiceRecording);
    document.getElementById('regRecordBtn').addEventListener('click', startVoiceRecording);
    document.getElementById('regStopBtn').addEventListener('click', stopVoiceRecording);
});

// Face Authentication Functions
async function startFaceAuth() {
    try {
        const username = document.getElementById('loginUsername').value;
        if (!username) {
            showStatus('loginStatus', 'Please enter your username first', 'danger');
            return;
        }
        
        currentAuthType = 'face';
        document.getElementById('biometricArea').style.display = 'block';
        document.getElementById('videoPreview').style.display = 'block';
        document.getElementById('audioControls').style.display = 'none';
        
        // Start camera
        currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
        document.getElementById('videoPreview').srcObject = currentStream;
        
        showStatus('loginStatus', 'Position your face in the camera and click Authenticate', 'info');
        document.getElementById('authenticateBtn').style.display = 'inline-block';
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        showStatus('loginStatus', 'Camera access denied or not available', 'danger');
    }
}

async function startVoiceAuth() {
    try {
        const username = document.getElementById('loginUsername').value;
        if (!username) {
            showStatus('loginStatus', 'Please enter your username first', 'danger');
            return;
        }
        
        currentAuthType = 'voice';
        document.getElementById('biometricArea').style.display = 'block';
        document.getElementById('videoPreview').style.display = 'none';
        document.getElementById('audioControls').style.display = 'block';
        
        showStatus('loginStatus', 'Click "Start Recording" and say the passphrase', 'info');
        
    } catch (error) {
        console.error('Error setting up voice auth:', error);
        showStatus('loginStatus', 'Voice authentication setup failed', 'danger');
    }
}

function authenticate() {
    const username = document.getElementById('loginUsername').value;
    const user = users.find(u => u.username === username);
    
    if (!user) {
        showStatus('loginStatus', 'User not found. Please register first.', 'danger');
        return;
    }
    
    if (currentAuthType === 'face') {
        // Simulate face recognition
        if (user.faceData) {
            // In a real system, you would compare the current face with stored biometric data
            setTimeout(() => {
                showStatus('loginStatus', 'Face authentication successful!', 'success');
                loginSuccess(user);
            }, 2000);
        } else {
            showStatus('loginStatus', 'No face data registered for this user', 'warning');
        }
    } else if (currentAuthType === 'voice') {
        // Simulate voice recognition
        if (user.voiceData) {
            setTimeout(() => {
                showStatus('loginStatus', 'Voice authentication successful!', 'success');
                loginSuccess(user);
            }, 2000);
        } else {
            showStatus('loginStatus', 'No voice data registered for this user', 'warning');
        }
    }
}

function cancelBiometric() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    document.getElementById('biometricArea').style.display = 'none';
    document.getElementById('authenticateBtn').style.display = 'none';
    currentAuthType = null;
    
    showStatus('loginStatus', 'Authentication cancelled', 'info');
}

// Registration Functions
async function captureFace() {
    try {
        document.getElementById('captureArea').style.display = 'block';
        document.getElementById('regVideo').style.display = 'block';
        document.getElementById('regCanvas').style.display = 'none';
        document.getElementById('regAudioControls').style.display = 'none';
        
        currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
        document.getElementById('regVideo').srcObject = currentStream;
        
        document.getElementById('captureBtn').style.display = 'inline-block';
        document.getElementById('captureBtn').onclick = () => saveBiometric('face');
        
        showStatus('registerStatus', 'Position your face and click Save when ready', 'info');
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        showStatus('registerStatus', 'Camera access denied or not available', 'danger');
    }
}

async function captureVoice() {
    try {
        document.getElementById('captureArea').style.display = 'block';
        document.getElementById('regVideo').style.display = 'none';
        document.getElementById('regAudioControls').style.display = 'block';
        
        showStatus('registerStatus', 'Click "Start Recording" to record your voice', 'info');
        
    } catch (error) {
        console.error('Error setting up voice capture:', error);
        showStatus('registerStatus', 'Voice capture setup failed', 'danger');
    }
}

function saveBiometric(type = null) {
    if (type === 'face' || currentAuthType === 'face') {
        // Capture face image
        const video = document.getElementById('regVideo');
        const canvas = document.getElementById('regCanvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        
        // Convert to base64 (in production, you'd process this for face recognition)
        const faceData = canvas.toDataURL('image/jpeg');
        
        showStatus('faceStatus', 'Face captured successfully!', 'success');
        
        // Store temporary face data
        window.tempFaceData = faceData;
        
        cancelCapture();
        
    } else if (currentAuthType === 'voice') {
        // Voice data would be processed here
        showStatus('voiceStatus', 'Voice recorded successfully!', 'success');
        window.tempVoiceData = recordedChunks;
        cancelCapture();
    }
}

function cancelCapture() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
    
    document.getElementById('captureArea').style.display = 'none';
    document.getElementById('captureBtn').style.display = 'none';
    
    // Reset audio recording
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    recordedChunks = [];
    
    currentAuthType = null;
}

// Voice Recording Functions
async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = function() {
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        
        // Update UI
        document.getElementById('recordBtn').classList.add('d-none');
        document.getElementById('stopBtn').classList.remove('d-none');
        document.getElementById('regRecordBtn').classList.add('d-none');
        document.getElementById('regStopBtn').classList.remove('d-none');
        
        showStatus('registerStatus', 'Recording... Say the passphrase clearly', 'info');
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        showStatus('registerStatus', 'Microphone access denied or not available', 'danger');
    }
}

function stopVoiceRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        
        // Update UI
        document.getElementById('recordBtn').classList.remove('d-none');
        document.getElementById('stopBtn').classList.add('d-none');
        document.getElementById('regRecordBtn').classList.remove('d-none');
        document.getElementById('regStopBtn').classList.add('d-none');
        
        if (document.getElementById('captureArea').style.display === 'block') {
            document.getElementById('captureBtn').style.display = 'inline-block';
            document.getElementById('captureBtn').onclick = () => saveBiometric('voice');
        } else {
            // This is for login voice auth
            document.getElementById('authenticateBtn').style.display = 'inline-block';
        }
        
        showStatus('registerStatus', 'Voice recorded! Click Save to store it.', 'success');
    }
}

// Form Handlers
function handlePasswordLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    const user = users.find(u => u.username === username && u.password === password);
    
    if (user) {
        showStatus('loginStatus', 'Password login successful!', 'success');
        loginSuccess(user);
    } else {
        showStatus('loginStatus', 'Invalid username or password', 'danger');
    }
}

function handleRegistration(event) {
    event.preventDefault();
    
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    
    // Check if user already exists
    if (users.find(u => u.username === username)) {
        showStatus('registerStatus', 'Username already exists', 'danger');
        return;
    }
    
    // Create new user
    const newUser = {
        username: username,
        email: email,
        password: password,
        faceData: window.tempFaceData || null,
        voiceData: window.tempVoiceData || null,
        registeredAt: new Date().toISOString()
    };
    
    users.push(newUser);
    
    // Clear temporary data
    window.tempFaceData = null;
    window.tempVoiceData = null;
    
    showStatus('registerStatus', 'Account created successfully! You can now login.', 'success');
    
    // Switch to login tab
    setTimeout(() => {
        document.querySelector('[href="#login"]').click();
        document.getElementById('registerForm').reset();
        document.getElementById('faceStatus').innerHTML = '';
        document.getElementById('voiceStatus').innerHTML = '';
    }, 2000);
}

function loginSuccess(user) {
    currentUser = user;
    
    // Update dashboard info
    document.getElementById('userInfo').textContent = `Welcome, ${user.username}!`;
    document.getElementById('lastLogin').textContent = new Date().toLocaleString();
    
    // Show dashboard tab
    document.getElementById('dashboardTab').style.display = 'block';
    document.querySelector('[href="#dashboard"]').click();
    
    // Clean up
    cancelBiometric();
    document.getElementById('loginForm').reset();
}

function logout() {
    currentUser = null;
    document.getElementById('dashboardTab').style.display = 'none';
    document.querySelector('[href="#login"]').click();
    showStatus('loginStatus', 'Logged out successfully', 'info');
}

// Utility Functions
function showStatus(elementId, message, type) {
    const statusElement = document.getElementById(elementId);
    statusElement.innerHTML = `
        <div class="alert alert-${type === 'danger' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} mt-3">
            ${message}
        </div>
    `;
    
    // Auto-hide success messages after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusElement.innerHTML = '';
        }, 3000);
    }
}