# app.py - Main Flask Application
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import pickle
import librosa
from datetime import datetime
import base64
import io
from PIL import Image
import sqlite3
import threading
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biometric_auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=True)
    voice_encoding = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.username}>'

class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    auth_method = db.Column(db.String(20), nullable=False)  # face, voice, password
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('login_history', lazy=True))

# Biometric Processing Classes
class FaceProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def extract_face_encoding(self, image_data):
        """Extract face encoding from image data"""
        try:
            # Convert image data to OpenCV format
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = image_data
                
            if image is None:
                return None
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return None
            
            # Get the largest face
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            
            # Extract face region
            face_region = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_resized = cv2.resize(face_region, (100, 100))
            
            # Flatten the face data as encoding
            face_encoding = face_resized.flatten()
            
            return face_encoding
            
        except Exception as e:
            logger.error(f"Face processing error: {str(e)}")
            return None
    
    def compare_faces(self, known_encoding, unknown_encoding, threshold=0.6):
        """Compare two face encodings"""
        try:
            if known_encoding is None or unknown_encoding is None:
                return False
                
            # Calculate similarity using correlation coefficient
            correlation = np.corrcoef(known_encoding, unknown_encoding)[0, 1]
            
            # Handle NaN values
            if np.isnan(correlation):
                return False
                
            return correlation > threshold
            
        except Exception as e:
            logger.error(f"Face comparison error: {str(e)}")
            return False

class VoiceProcessor:
    def __init__(self):
        self.sample_rate = 22050
        self.n_mfcc = 13
        
    def extract_voice_encoding(self, audio_data):
        """Extract voice features from audio data"""
        try:
            # Load audio data
            if isinstance(audio_data, bytes):
                # Convert bytes to audio array
                audio_buffer = io.BytesIO(audio_data)
                y, sr = librosa.load(audio_buffer, sr=self.sample_rate)
            else:
                y, sr = librosa.load(audio_data, sr=self.sample_rate)
            
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            
            # Take mean of features over time
            voice_encoding = np.mean(mfccs, axis=1)
            
            return voice_encoding
            
        except Exception as e:
            logger.error(f"Voice processing error: {str(e)}")
            return None
    
    def compare_voices(self, known_encoding, unknown_encoding, threshold=0.85):
        """Compare two voice encodings"""
        try:
            if known_encoding is None or unknown_encoding is None:
                return False
                
            # Calculate cosine similarity
            dot_product = np.dot(known_encoding, unknown_encoding)
            norm_a = np.linalg.norm(known_encoding)
            norm_b = np.linalg.norm(unknown_encoding)
            
            if norm_a == 0 or norm_b == 0:
                return False
                
            similarity = dot_product / (norm_a * norm_b)
            
            return similarity > threshold
            
        except Exception as e:
            logger.error(f"Voice comparison error: {str(e)}")
            return False

# Initialize processors
face_processor = FaceProcessor()
voice_processor = VoiceProcessor()

# Routes
@app.route('/')
def index():
    """Serve the main application page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user with biometric data"""
    try:
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        face_data = request.files.get('face_data')
        voice_data = request.files.get('voice_data')
        
        # Validate input
        if not all([username, email, password]):
            return jsonify({
                'success': False,
                'message': 'Username, email, and password are required'
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 409
            
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'Email already exists'
            }), 409
        
        # Process biometric data
        face_encoding = None
        voice_encoding = None
        
        if face_data:
            face_bytes = face_data.read()
            face_encoding = face_processor.extract_face_encoding(face_bytes)
            if face_encoding is None:
                return jsonify({
                    'success': False,
                    'message': 'Could not process face data. Please ensure your face is clearly visible.'
                }), 400
        
        if voice_data:
            voice_bytes = voice_data.read()
            voice_encoding = voice_processor.extract_voice_encoding(voice_bytes)
            if voice_encoding is None:
                return jsonify({
                    'success': False,
                    'message': 'Could not process voice data. Please ensure clear audio recording.'
                }), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            face_encoding=pickle.dumps(face_encoding) if face_encoding is not None else None,
            voice_encoding=pickle.dumps(voice_encoding) if voice_encoding is not None else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {username}")
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again.'
        }), 500

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate user with various methods"""
    try:
        username = request.form.get('username')
        auth_type = request.form.get('auth_type')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username is required'
            }), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Invalid username or account disabled'
            }), 401
        
        success = False
        auth_method = auth_type
        
        # Authenticate based on method
        if auth_type == 'password':
            password = request.form.get('password')
            if password and check_password_hash(user.password_hash, password):
                success = True
                
        elif auth_type == 'face':
            biometric_data = request.files.get('biometric_data')
            if biometric_data and user.face_encoding:
                face_bytes = biometric_data.read()
                current_encoding = face_processor.extract_face_encoding(face_bytes)
                stored_encoding = pickle.loads(user.face_encoding)
                
                if current_encoding is not None and stored_encoding is not None:
                    success = face_processor.compare_faces(stored_encoding, current_encoding)
                    
        elif auth_type == 'voice':
            biometric_data = request.files.get('biometric_data')
            if biometric_data and user.voice_encoding:
                voice_bytes = biometric_data.read()
                current_encoding = voice_processor.extract_voice_encoding(voice_bytes)
                stored_encoding = pickle.loads(user.voice_encoding)
                
                if current_encoding is not None and stored_encoding is not None:
                    success = voice_processor.compare_voices(stored_encoding, current_encoding)
        
        # Log authentication attempt
        log_entry = LoginHistory(
            user_id=user.id,
            auth_method=auth_method,
            success=success,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(log_entry)
        
        if success:
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Successful {auth_type} authentication for user: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'last_login': user.last_login.isoformat()
                }
            })
        else:
            db.session.commit()
            logger.warning(f"Failed {auth_type} authentication for user: {username}")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed'
            }), 401
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Authentication error. Please try again.'
        }), 500

@app.route('/api/user/<int:user_id>/history', methods=['GET'])
def get_user_history(user_id):
    """Get user login history"""
    try:
        user = User.query.get_or_404(user_id)
        
        history = LoginHistory.query.filter_by(user_id=user_id)\
                                   .order_by(LoginHistory.timestamp.desc())\
                                   .limit(50).all()
        
        history_data = []
        for entry in history:
            history_data.append({
                'id': entry.id,
                'auth_method': entry.auth_method,
                'success': entry.success,
                'ip_address': entry.ip_address,
                'timestamp': entry.timestamp.isoformat()
            })
        
        return jsonify({
            'success': True,
            'history': history_data
        })
        
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Could not retrieve history'
        }), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users (admin function)"""
    try:
        users = User.query.all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active,
                'has_face_data': user.face_encoding is not None,
                'has_voice_data': user.voice_encoding is not None
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        logger.error(f"Users retrieval error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Could not retrieve users'
        }), 500

@app.route('/api/user/<int:user_id>/update-biometric', methods=['POST'])
def update_biometric(user_id):
    """Update user's biometric data"""
    try:
        user = User.query.get_or_404(user_id)
        biometric_type = request.form.get('type')  # 'face' or 'voice'
        biometric_data = request.files.get('biometric_data')
        
        if not biometric_type or not biometric_data:
            return jsonify({
                'success': False,
                'message': 'Biometric type and data are required'
            }), 400
        
        if biometric_type == 'face':
            face_bytes = biometric_data.read()
            face_encoding = face_processor.extract_face_encoding(face_bytes)
            
            if face_encoding is None:
                return jsonify({
                    'success': False,
                    'message': 'Could not process face data'
                }), 400
            
            user.face_encoding = pickle.dumps(face_encoding)
            
        elif biometric_type == 'voice':
            voice_bytes = biometric_data.read()
            voice_encoding = voice_processor.extract_voice_encoding(voice_bytes)
            
            if voice_encoding is None:
                return jsonify({
                    'success': False,
                    'message': 'Could not process voice data'
                }), 400
            
            user.voice_encoding = pickle.dumps(voice_encoding)
        
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid biometric type'
            }), 400
        
        db.session.commit()
        
        logger.info(f"Updated {biometric_type} data for user: {user.username}")
        
        return jsonify({
            'success': True,
            'message': f'{biometric_type.title()} data updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Biometric update error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Could not update biometric data'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# Database initialization
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)