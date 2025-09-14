# biometric_utils.py - Advanced biometric processing utilities
import cv2
import numpy as np
import librosa
from scipy.spatial.distance import cosine
from sklearn.preprocessing import normalize
import logging

logger = logging.getLogger(__name__)

class AdvancedFaceProcessor:
    """Advanced face processing with liveness detection"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
    def detect_liveness(self, image):
        """Simple liveness detection based on eye and face features"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) == 0:
                return False, "No face detected"
            
            # Get the largest face
            (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
            face_roi = gray[y:y+h, x:x+w]
            
            # Detect eyes within face region
            eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 3)
            
            # Basic liveness checks
            if len(eyes) < 2:
                return False, "Eyes not clearly visible"
            
            # Check face size (too small might indicate photo)
            if w < 100 or h < 100:
                return False, "Face too small or distant"
            
            # Check brightness variation (photos tend to be more uniform)
            brightness_std = np.std(face_roi)
            if brightness_std < 20:
                return False, "Image appears too uniform (possible photo)"
            
            return True, "Liveness check passed"
            
        except Exception as e:
            logger.error(f"Liveness detection error: {str(e)}")
            return False, "Liveness detection failed"
    
    def extract_advanced_features(self, image_data):
        """Extract advanced facial features using multiple techniques"""
        try:
            # Convert to OpenCV format
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = image_data
            
            if image is None:
                return None, "Invalid image data"
            
            # Liveness detection
            is_live, liveness_msg = self.detect_liveness(image)
            if not is_live:
                return None, liveness_msg
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return None, "No face detected"
            
            # Get the largest face
            (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
            face_region = gray[y:y+h, x:x+w]
            
            # Multiple feature extraction methods
            features = {}
            
            # 1. Basic pixel features (resized face)
            face_resized = cv2.resize(face_region, (100, 100))
            features['pixel_features'] = face_resized.flatten()
            
            # 2. Histogram of Oriented Gradients (HOG)
            # Compute gradients
            grad_x = cv2.Sobel(face_region, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(face_region, cv2.CV_64F, 0, 1, ksize=3)
            
            # Compute magnitude and angle
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            angle = np.arctan2(grad_y, grad_x) * 180 / np.pi
            
            # Create HOG features (simplified)
            hist, _ = np.histogram(angle.flatten(), bins=36, range=(-180, 180), weights=magnitude.flatten())
            features['hog_features'] = hist
            
            # 3. Local Binary Pattern (LBP) features
            lbp_features = self.compute_lbp(face_region)
            features['lbp_features'] = lbp_features
            
            # 4. Geometric features
            geometric_features = self.extract_geometric_features(face_region, faces[0])
            features['geometric_features'] = geometric_features
            
            # Combine all features
            combined_features = np.concatenate([
                features['pixel_features'] / 255.0,  # Normalize pixels
                features['hog_features'] / np.max(features['hog_features']),  # Normalize HOG
                features['lbp_features'] / np.max(features['lbp_features']),  # Normalize LBP
                features['geometric_features']
            ])
            
            return combined_features, "Features extracted successfully"
            
        except Exception as e:
            logger.error(f"Advanced face processing error: {str(e)}")
            return None, f"Processing error: {str(e)}"
    
    def compute_lbp(self, image):
        """Compute Local Binary Pattern features"""
        try:
            rows, cols = image.shape
            lbp_image = np.zeros_like(image)
            
            for i in range(1, rows-1):
                for j in range(1, cols-1):
                    center = image[i, j]
                    pattern = 0
                    
                    # Compare with 8 neighbors
                    neighbors = [
                        image[i-1, j-1], image[i-1, j], image[i-1, j+1],
                        image[i, j+1], image[i+1, j+1], image[i+1, j],
                        image[i+1, j-1], image[i, j-1]
                    ]
                    
                    for k, neighbor in enumerate(neighbors):
                        if neighbor >= center:
                            pattern |= (1 << k)
                    
                    lbp_image[i, j] = pattern
            
            # Create histogram of LBP patterns
            hist, _ = np.histogram(lbp_image.flatten(), bins=256, range=(0, 256))
            return hist
            
        except Exception as e:
            logger.error(f"LBP computation error: {str(e)}")
            return np.zeros(256)
    
    def extract_geometric_features(self, face_region, face_coords):
        """Extract geometric features from face"""
        try:
            x, y, w, h = face_coords
            
            # Basic geometric measurements
            aspect_ratio = w / h
            face_area = w * h
            
            # Eye detection within face
            eyes = self.eye_cascade.detectMultiScale(face_region, 1.1, 3)
            eye_count = len(eyes)
            
            # Calculate eye distance if two eyes detected
            eye_distance = 0
            if len(eyes) >= 2:
                eye1, eye2 = eyes[0], eyes[1]
                eye_distance = np.sqrt((eye1[0] - eye2[0])**2 + (eye1[1] - eye2[1])**2)
            
            # Smile detection
            smiles = self.smile_cascade.detectMultiScale(face_region, 1.8, 20)
            smile_detected = len(smiles) > 0
            
            return np.array([
                aspect_ratio,
                face_area / 10000,  # Normalize
                eye_count,
                eye_distance / 100,  # Normalize
                float(smile_detected)
            ])
            
        except Exception as e:
            logger.error(f"Geometric feature extraction error: {str(e)}")
            return np.zeros(5)

class AdvancedVoiceProcessor:
    """Advanced voice processing with speaker verification"""
    
    def __init__(self):
        self.sample_rate = 22050
        self.n_mfcc = 13
        self.n_mels = 40
        
    def extract_advanced_features(self, audio_data):
        """Extract comprehensive voice features"""
        try:
            # Load audio
            if isinstance(audio_data, bytes):
                import io
                audio_buffer = io.BytesIO(audio_data)
                y, sr = librosa.load(audio_buffer, sr=self.sample_rate)
            else:
                y, sr = librosa.load(audio_data, sr=self.sample_rate)
            
            if len(y) == 0:
                return None, "Empty audio data"
            
            # Voice activity detection (simple energy-based)
            if not self.detect_voice_activity(y):
                return None, "No voice activity detected"
            
            features = {}
            
            # 1. MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            features['mfcc'] = np.mean(mfccs, axis=1)
            features['mfcc_std'] = np.std(mfccs, axis=1)
            
            # 2. Mel-spectrogram features
            mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels)
            features['mel'] = np.mean(mel_spec, axis=1)
            
            # 3. Chroma features (pitch-related)
            chroma = librosa.feature.chroma(y=y, sr=sr)
            features['chroma'] = np.mean(chroma, axis=1)
            
            # 4. Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            
            features['spectral'] = np.array([
                np.mean(spectral_centroids),
                np.mean(spectral_rolloff),
                np.mean(spectral_bandwidth)
            ])
            
            # 5. Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)
            features['zcr'] = np.mean(zcr)
            
            # 6. Fundamental frequency (F0) estimation
            f0 = self.estimate_f0(y, sr)
            features['f0'] = f0
            
            # 7. Voice quality features
            voice_quality = self.extract_voice_quality(y, sr)
            features['voice_quality'] = voice_quality
            
            # Combine all features
            combined_features = np.concatenate([
                features['mfcc'],
                features['mfcc_std'],
                features['mel'] / np.max(features['mel']),  # Normalize
                features['chroma'],
                features['spectral'] / np.max(features['spectral']),  # Normalize
                [features['zcr']],
                features['f0'],
                features['voice_quality']
            ])
            
            return combined_features, "Voice features extracted successfully"
            
        except Exception as e:
            logger.error(f"Advanced voice processing error: {str(e)}")
            return None, f"Processing error: {str(e)}"
    
    def detect_voice_activity(self, audio_signal, threshold=0.01):
        """Simple voice activity detection based on energy"""
        try:
            # Calculate energy
            energy = np.mean(audio_signal ** 2)
            return energy > threshold
        except:
            return False
    
    def estimate_f0(self, y, sr):
        """Estimate fundamental frequency"""
        try:
            # Simple autocorrelation-based F0 estimation
            autocorr = np.correlate(y, y, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peaks
            peaks = []
            for i in range(1, len(autocorr)-1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    peaks.append((i, autocorr[i]))
            
            if not peaks:
                return np.array([0, 0, 0])
            
            # Sort by amplitude
            peaks.sort(key=lambda x: x[1], reverse=True)
            
            # Convert to frequency
            if len(peaks) > 0:
                f0_period = peaks[0][0]
                f0_freq = sr / f0_period if f0_period > 0 else 0
                f0_strength = peaks[0][1]
                
                return np.array([
                    f0_freq / 1000,  # Normalize to kHz
                    f0_strength / np.max(autocorr),  # Normalize strength
                    len(peaks)  # Number of harmonics
                ])
            
            return np.array([0, 0, 0])
            
        except Exception as e:
            logger.error(f"F0 estimation error: {str(e)}")
            return np.array([0, 0, 0])
    
    def extract_voice_quality(self, y, sr):
        """Extract voice quality features"""
        try:
            # Jitter (frequency variation)
            if len(y) > sr:  # At least 1 second of audio
                frame_length = int(0.025 * sr)  # 25ms frames
                hop_length = int(0.01 * sr)     # 10ms hop
                
                frames = librosa.util.frame(y, frame_length=frame_length, 
                                          hop_length=hop_length, axis=0)
                
                # Calculate frame-to-frame frequency variation
                frame_energies = np.mean(frames ** 2, axis=1)
                jitter = np.std(frame_energies) / (np.mean(frame_energies) + 1e-8)
                
                # Shimmer (amplitude variation)
                shimmer = np.std(np.abs(y)) / (np.mean(np.abs(y)) + 1e-8)
                
                # Harmonics-to-noise ratio (simplified)
                fft = np.fft.fft(y)
                magnitude = np.abs(fft)
                harmonics = np.sum(magnitude[:len(magnitude)//4])  # Lower frequencies
                noise = np.sum(magnitude[len(magnitude)//4:])      # Higher frequencies
                hnr = harmonics / (noise + 1e-8)
                
                return np.array([jitter, shimmer, np.log(hnr + 1)])
            
            return np.array([0, 0, 0])
            
        except Exception as e:
            logger.error(f"Voice quality extraction error: {str(e)}")
            return np.array([0, 0, 0])

class BiometricMatcher:
    """Advanced biometric matching algorithms"""
    
    @staticmethod
    def cosine_similarity(features1, features2):
        """Calculate cosine similarity between feature vectors"""
        try:
            # Normalize features
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
            
            normalized1 = features1 / norm1
            normalized2 = features2 / norm2
            
            similarity = np.dot(normalized1, normalized2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Cosine similarity error: {str(e)}")
            return 0
    
    @staticmethod
    def euclidean_distance(features1, features2):
        """Calculate normalized Euclidean distance"""
        try:
            distance = np.linalg.norm(features1 - features2)
            max_distance = np.sqrt(len(features1))  # Maximum possible distance
            normalized_distance = distance / max_distance
            similarity = 1 - normalized_distance  # Convert to similarity
            return float(max(0, similarity))
            
        except Exception as e:
            logger.error(f"Euclidean distance error: {str(e)}")
            return 0
    
    @staticmethod
    def weighted_similarity(similarities, weights=None):
        """Calculate weighted similarity score"""
        try:
            if weights is None:
                weights = np.ones(len(similarities)) / len(similarities)
            
            weighted_score = np.average(similarities, weights=weights)
            return float(weighted_score)
            
        except Exception as e:
            logger.error(f"Weighted similarity error: {str(e)}")
            return 0

# Utility functions for production use
def validate_biometric_quality(biometric_data, data_type):
    """Validate the quality of biometric data"""
    try:
        if data_type == 'face':
            processor = AdvancedFaceProcessor()
            features, message = processor.extract_advanced_features(biometric_data)
            return features is not None, message
            
        elif data_type == 'voice':
            processor = AdvancedVoiceProcessor()
            features, message = processor.extract_advanced_features(biometric_data)
            return features is not None, message
            
        return False, "Unknown biometric type"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def compare_biometrics(stored_features, current_features, biometric_type, threshold=None):
    """Compare biometric features with multiple algorithms"""
    try:
        if stored_features is None or current_features is None:
            return False, 0.0, "Missing feature data"
        
        # Set default thresholds
        if threshold is None:
            threshold = 0.7 if biometric_type == 'face' else 0.85
        
        # Calculate multiple similarity scores
        cosine_sim = BiometricMatcher.cosine_similarity(stored_features, current_features)
        euclidean_sim = BiometricMatcher.euclidean_distance(stored_features, current_features)
        
        # Weighted combination (cosine similarity weighted more heavily)
        weights = [0.7, 0.3]  # Favor cosine similarity
        combined_score = BiometricMatcher.weighted_similarity([cosine_sim, euclidean_sim], weights)
        
        is_match = combined_score >= threshold
        
        return is_match, combined_score, f"Match: {is_match}, Score: {combined_score:.3f}"
        
    except Exception as e:
        logger.error(f"Biometric comparison error: {str(e)}")
        return False, 0.0, f"Comparison error: {str(e)}"