# Face-voice-Authentication-website
🔐 Face & Voice Authentication System

A secure web-based authentication system that verifies users using Face Recognition and Voice Recognition instead of traditional password-based login methods.
This project was developed as a team-based major project to implement AI-powered multi-factor biometric authentication for enhanced security and real-world applications.

👥 Team Members
K Sudeep Gouda,
Afsa saboo,
B Sai dikshitha

📌 Project Overview
Traditional password systems are vulnerable to hacking, phishing, and brute-force attacks.
This system improves security by combining:

👤 Face Recognition
🎤 Voice Recognition
Access is granted only when both biometrics match successfully.

🚀 Key Features

Real-time Face Detection using Webcam
Voice Authentication using Microphone
Multi-Factor Biometric Verification
AI-Based Identity Matching
Secure User Registration & Login
MySQL Database Integration
User-Friendly Web Interface

🛠️ Technologies Used
🔹 Frontend

HTML
CSS
JavaScript
🔹 Backend
Python (Flask Framework)
Node.js (if applicable)
🔹 Libraries & Tools
OpenCV
SpeechRecognition
NumPy
Scikit-learn
PyAudio
🔹 Database
MySQL

📂 Project Structure
PROJECT/
│
├── backend/                 # Backend logic and AI models
├── frontend/                # Frontend files (UI)
├── static/                  # Static assets
├── uploads/                 # Stored biometric samples
├── instance/                # Database instance files
├── Documentation/           # Project documentation
├── Testing & Deployment/    # Testing & deployment files
│
├── package.json
├── package-lock.json
├── Local MySQL.session.sql
├── README.md
├── .gitignore

⚙️ How the System Works
📝 Registration Phase

User enters personal details.
Webcam captures face data.
Microphone records voice sample.
Biometric features are extracted.
Data is securely stored in the database.
🔐 Authentication Phase
User attempts login.
Live face is captured and analyzed.
Live voice sample is recorded.
System compares both with stored biometric data.
If matched → ✅ Access Granted
If mismatch → ❌ Access Denied

💻 Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name

2️⃣ Backend Setup
cd backend
pip install -r requirements.txt
python app.py

3️⃣ Frontend Setup
cd frontend
npm install
npm start


Open in browser:
http://localhost:5000

🔒 Security Advantages
Eliminates password dependency
Hard to spoof
Dual biometric authentication
Real-time verification
Improved data protection

🔮 Future Enhancements
Liveness Detection (Anti-Spoofing)
Deep Learning-based Face Recognition (CNN Models)
Encrypted Biometric Storage
Cloud Deployment (AWS / Azure)
Mobile Application Integration

🌍 Real-World Applications

Banking Authentication Systems
Online Examination Portals
Government Secure Portals
Smart Attendance Systems
Enterprise Access Control

🎓 Academic Information

Developed as a Major Project for
Bachelor of Engineering – Computer Science & Engineering (AI)

📜 License

This project is developed for academic and educational purposes.

