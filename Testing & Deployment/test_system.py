# test_system.py - Comprehensive system testing
import unittest
import json
import os
import tempfile
import numpy as np
from app import app, db, User
from biometric_utils import AdvancedFaceProcessor, AdvancedVoiceProcessor, BiometricMatcher

class BiometricAuthTestCase(unittest.TestCase):
    """Test cases for biometric authentication system"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_user_registration_without_biometrics(self):
        """Test user registration with password only"""
        response = self.client.post('/api/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 400)  # Should require biometrics
    
    def test_user_registration_duplicate_username(self):
        """Test duplicate username registration"""
        # Create first user
        with self.app.app_context():
            user = User(
                username='testuser',
                email='test1@example.com',
                password_hash='hash'
            )
            db.session.add(user)
            db.session.commit()
        
        # Try to create duplicate
        response = self.client.post('/api/register', data={
            'username': 'testuser',
            'email': 'test2@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 409)
    
    def test_password_authentication(self):
        """Test password-based authentication"""
        # First register a user
        with self.app.app_context():
            from werkzeug.security import generate_password_hash
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(user)
            db.session.commit()
        
        # Test authentication
        response = self.client.post('/api/authenticate', data={
            'username': 'testuser',
            'password': 'testpass123',
            'auth_type': 'password'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_invalid_password_authentication(self):
        """Test authentication with wrong password"""
        # Register user
        with self.app.app_context():
            from werkzeug.security import generate_password_hash
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(user)
            db.session.commit()
        
        # Test wrong password
        response = self.client.post('/api/authenticate', data={
            'username': 'testuser',
            'password': 'wrongpass',
            'auth_type': 'password'
        })
        
        self.assertEqual(response.status_code, 401)
    
    def test_nonexistent_user_authentication(self):
        """Test authentication with non-existent user"""
        response = self.client.post('/api/authenticate', data={
            'username': 'nonexistent',
            'password': 'anypass',
            'auth_type': 'password'
        })
        
        self.assertEqual(response.status_code, 401)

class BiometricProcessingTestCase(unittest.TestCase):
    """Test cases for biometric processing functions"""
    
    def test_face_processor_initialization(self):
        """Test face processor initialization"""
        processor = AdvancedFaceProcessor()
        self.assertIsNotNone(processor.face_cascade)
        self.assertIsNotNone(processor.eye_cascade)
    
    def test_voice_processor_initialization(self):
        """Test voice processor initialization"""
        processor = AdvancedVoiceProcessor()
        self.assertEqual(processor.sample_rate, 22050)
        self.assertEqual(processor.n_mfcc, 13)
    
    def test_biometric_matcher_cosine_similarity(self):
        """Test cosine similarity calculation"""
        features1 = np.array([1, 2, 3, 4, 5])
        features2 = np.array([2, 4, 6, 8, 10])  # Scaled version
        
        similarity = BiometricMatcher.cosine_similarity(features1, features2)
        self.assertAlmostEqual(similarity, 1.0, places=5)  # Should be very similar
    
    def test_biometric_matcher_euclidean_distance(self):
        """Test Euclidean distance calculation"""
        features1 = np.array([1, 1, 1, 1, 1])
        features2 = np.array([1, 1, 1, 1, 1])  # Identical
        
        similarity = BiometricMatcher.euclidean_distance(features1, features2)
        self.assertAlmostEqual(similarity, 1.0, places=5)  # Should be identical
    
    def test_weighted_similarity(self):
        """Test weighted similarity calculation"""
        similarities = [0.8, 0.6, 0.9]
        weights = [0.5, 0.2, 0.3]
        
        weighted_sim = BiometricMatcher.weighted_similarity(similarities, weights)
        expected = 0.8 * 0.5 + 0.6 * 0.2 + 0.9 * 0.3
        self.assertAlmostEqual(weighted_sim, expected, places=5)

class IntegrationTestCase(unittest.TestCase):
    """Integration tests for the entire system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def test_full_registration_flow(self):
        """Test complete user registration flow"""
        # This would require actual image and audio data
        # For now, just test the endpoint structure
        response = self.client.post('/api/register')
        self.assertIn(response.status_code, [400, 401])  # Should fail without data
    
    def test_api_endpoints_structure(self):
        """Test that all required API endpoints exist"""
        endpoints_to_test = [
            ('/api/health', 'GET'),
            ('/api/register', 'POST'),
            ('/api/authenticate', 'POST'),
            ('/api/users', 'GET')
        ]
        
        for endpoint, method in endpoints_to_test:
            if method == 'GET':
                response = self.client.get(endpoint)
            else:
                response = self.client.post(endpoint)
            
            # Should not return 404 (endpoint exists)
            self.assertNotEqual(response.status_code, 404, 
                               f"Endpoint {endpoint} not found")

def run_performance_tests():
    """Run performance tests for biometric processing"""
    print("\n🔄 Running Performance Tests...")
    
    # Test face processing performance
    print("Testing face processing performance...")
    face_processor = AdvancedFaceProcessor()
    
    # Create dummy image data
    dummy_image = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    
    import time
    start_time = time.time()
    features, message = face_processor.extract_advanced_features(dummy_image)
    face_processing_time = time.time() - start_time
    
    print(f"Face processing time: {face_processing_time:.3f} seconds")
    
    # Test voice processing performance
    print("Testing voice processing performance...")
    voice_processor = AdvancedVoiceProcessor()
    
    # Create dummy audio data (1 second of random noise)
    sample_rate = 22050
    dummy_audio = np.random.randn(sample_rate)
    
    start_time = time.time()
    features, message = voice_processor.extract_advanced_features(dummy_audio)
    voice_processing_time = time.time() - start_time
    
    print(f"Voice processing time: {voice_processing_time:.3f} seconds")
    
    # Performance benchmarks
    if face_processing_time > 2.0:
        print("⚠️  Face processing is slower than expected (>2s)")
    else:
        print("✅ Face processing performance is acceptable")
    
    if voice_processing_time > 1.0:
        print("⚠️  Voice processing is slower than expected (>1s)")
    else:
        print("✅ Voice processing performance is acceptable")

def run_security_tests():
    """Run basic security tests"""
    print("\n🔒 Running Security Tests...")
    
    # Test SQL injection protection (basic)
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Test malicious username
    response = client.post('/api/authenticate', data={
        'username': "admin'; DROP TABLE users; --",
        'password': 'anypass',
        'auth_type': 'password'
    })
    
    # Should handle gracefully, not crash
    print(f"SQL injection test response: {response.status_code}")
    
    # Test XSS protection (basic)
    response = client.post('/api/register', data={
        'username': '<script>alert("xss")</script>',
        'email': 'test@example.com',
        'password': 'testpass'
    })
    
    print(f"XSS protection test response: {response.status_code}")
    print("✅ Basic security tests completed")

if __name__ == '__main__':
    print("🧪 Starting Biometric Authentication System Tests")
    print("=" * 50)
    
    # Run unit tests
    print("\n📋 Running Unit Tests...")
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(BiometricAuthTestCase)
    )
    
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(BiometricProcessingTestCase)
    )
    
    unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromTestCase(IntegrationTestCase)
    )
    
    # Run performance tests
    run_performance_tests()
    
    # Run security tests
    run_security_tests()
    
    print("\n✅ All tests completed!")
    print("=" * 50)