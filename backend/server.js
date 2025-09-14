// server.js - Node.js backend with Express and MySQL
const path = require('path');
const express = require('express');
const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
const cors = require('cors');
const multer = require('multer');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors({
    origin: ['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3001'],
    credentials: true
}));
app.use(express.json({ limit: '50mb' })); // Large limit for image data
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.static(path.join(__dirname, '../frontend/public')));
app.use(express.static('public')); // Serve your HTML file from public folder

// MySQL connection configuration
const dbConfig = {
    host: 'localhost',
    user: 'root',
    password: 'Sudeep@9380',
    database: 'biometric_auth',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
};

// Create connection pool
const pool = mysql.createPool(dbConfig);

// Test database connection
async function testConnection() {
    try {
        const connection = await pool.getConnection();
        console.log('✅ Connected to MySQL database');
        connection.release();
    } catch (error) {
        console.error('❌ Database connection failed:', error.message);
    }
}

// Serve the main HTML file at root
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/public/index.html'));
});

// Routes

// Get all users (for admin/debugging - remove in production)
app.get('/api/users', async (req, res) => {
    try {
        const [rows] = await pool.execute(
            'SELECT id, username, email, created_at, last_login FROM users'
        );
        res.json({ success: true, users: rows });
    } catch (error) {
        console.error('Error fetching users:', error);
        res.status(500).json({ success: false, message: 'Database error' });
    }
});

// Register new user
app.post('/api/register', async (req, res) => {
    try {
        const { username, email, password, faceData, voiceData } = req.body;
        
        // Validate input
        if (!username || !email || !password) {
            return res.status(400).json({ 
                success: false, 
                message: 'Username, email, and password are required' 
            });
        }
        
        // Check if user already exists
        const [existing] = await pool.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            [username, email]
        );
        
        if (existing.length > 0) {
            return res.status(400).json({ 
                success: false, 
                message: 'Username or email already exists' 
            });
        }
        
        // Hash password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);
        
        // Insert user into database - FIXED: using password_hash column
        const [result] = await pool.execute(
            `INSERT INTO users (username, email, password_hash, face_data, voice_data) 
             VALUES (?, ?, ?, ?, ?)`,
            [username, email, hashedPassword, faceData, voiceData]
        );
        
        console.log('✅ User registered:', { 
            id: result.insertId, 
            username, 
            email,
            hasFaceData: !!faceData,
            hasVoiceData: !!voiceData 
        });
        
        res.json({ 
            success: true, 
            message: 'User registered successfully',
            userId: result.insertId 
        });
        
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ success: false, message: 'Registration failed' });
    }
});

// Login with password
app.post('/api/login/password', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        // Get user from database
        const [rows] = await pool.execute(
            'SELECT * FROM users WHERE username = ?',
            [username]
        );
        
        if (rows.length === 0) {
            return res.status(401).json({ 
                success: false, 
                message: 'Invalid username or password' 
            });
        }
        
        const user = rows[0];
        
        // Verify password - FIXED: using password_hash column
        const passwordMatch = await bcrypt.compare(password, user.password_hash);
        
        if (!passwordMatch) {
            return res.status(401).json({ 
                success: false, 
                message: 'Invalid username or password' 
            });
        }
        
        // Update last login
        await pool.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            [user.id]
        );
        
        // Log login attempt - FIXED: using your table structure
        await pool.execute(
            'INSERT INTO login_attempts (username, auth_type, success) VALUES (?, ?, ?)',
            [username, 'password', true]
        );
        
        console.log('✅ Password login successful:', { username, userId: user.id });
        
        res.json({ 
            success: true, 
            message: 'Login successful',
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                lastLogin: user.last_login
            }
        });
        
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ success: false, message: 'Login failed' });
    }
});

// Face authentication
app.post('/api/login/face', async (req, res) => {
    try {
        const { username, faceData } = req.body;
        
        // Get user from database
        const [rows] = await pool.execute(
            'SELECT * FROM users WHERE username = ?',
            [username]
        );
        
        if (rows.length === 0 || !rows[0].face_data) {
            return res.status(401).json({ 
                success: false, 
                message: 'User not found or no face data registered' 
            });
        }
        
        const user = rows[0];
        
        // In production, use a proper face recognition service
        const similarity = await compareFaceData(faceData, user.face_data);
        
        if (similarity > 0.7) { // 70% threshold
            // Update last login
            await pool.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                [user.id]
            );
            
            // Log login attempt - FIXED: using your table structure
            await pool.execute(
                'INSERT INTO login_attempts (username, auth_type, success) VALUES (?, ?, ?)',
                [username, 'face', true]
            );
            
            console.log('✅ Face login successful:', { username, userId: user.id });
            
            res.json({ 
                success: true, 
                message: 'Face authentication successful',
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    lastLogin: new Date()
                }
            });
        } else {
            // Log failed attempt - FIXED: using your table structure
            await pool.execute(
                'INSERT INTO login_attempts (username, auth_type, success) VALUES (?, ?, ?)',
                [username, 'face', false]
            );
            
            res.status(401).json({ 
                success: false, 
                message: 'Face does not match' 
            });
        }
        
    } catch (error) {
        console.error('Face auth error:', error);
        res.status(500).json({ success: false, message: 'Face authentication failed' });
    }
});

// Voice authentication
app.post('/api/login/voice', async (req, res) => {
    try {
        const { username, voiceData } = req.body;
        
        // Get user from database
        const [rows] = await pool.execute(
            'SELECT * FROM users WHERE username = ?',
            [username]
        );
        
        if (rows.length === 0 || !rows[0].voice_data) {
            return res.status(401).json({ 
                success: false, 
                message: 'User not found or no voice data registered' 
            });
        }
        
        const user = rows[0];
        
        // In production, use a voice recognition service
        const isMatch = Math.random() > 0.3; // 70% success rate for demo
        
        if (isMatch) {
            // Update last login
            await pool.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                [user.id]
            );
            
            // Log login attempt - FIXED: using your table structure
            await pool.execute(
                'INSERT INTO login_attempts (username, auth_type, success) VALUES (?, ?, ?)',
                [username, 'voice', true]
            );
            
            console.log('✅ Voice login successful:', { username, userId: user.id });
            
            res.json({ 
                success: true, 
                message: 'Voice authentication successful',
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    lastLogin: new Date()
                }
            });
        } else {
            // Log failed attempt - FIXED: using your table structure
            await pool.execute(
                'INSERT INTO login_attempts (username, auth_type, success) VALUES (?, ?, ?)',
                [username, 'voice', false]
            );
            
            res.status(401).json({ 
                success: false, 
                message: 'Voice does not match' 
            });
        }
        
    } catch (error) {
        console.error('Voice auth error:', error);
        res.status(500).json({ success: false, message: 'Voice authentication failed' });
    }
});

// Get user profile
app.get('/api/user/:id', async (req, res) => {
    try {
        const userId = req.params.id;
        
        const [rows] = await pool.execute(
            'SELECT id, username, email, created_at, last_login FROM users WHERE id = ?',
            [userId]
        );
        
        if (rows.length === 0) {
            return res.status(404).json({ success: false, message: 'User not found' });
        }
        
        res.json({ success: true, user: rows[0] });
        
    } catch (error) {
        console.error('Error fetching user:', error);
        res.status(500).json({ success: false, message: 'Database error' });
    }
});

// Get login history - FIXED: using your table structure
app.get('/api/user/:username/history', async (req, res) => {
    try {
        const username = req.params.username;
        
        const [rows] = await pool.execute(`
            SELECT auth_type, attempt_time, success 
            FROM login_attempts 
            WHERE username = ? 
            ORDER BY attempt_time DESC 
            LIMIT 10
        `, [username]);
        
        res.json({ success: true, history: rows });
        
    } catch (error) {
        console.error('Error fetching login history:', error);
        res.status(500).json({ success: false, message: 'Database error' });
    }
});

// Helper function for face comparison (placeholder)
async function compareFaceData(currentFace, storedFace) {
    // In production, integrate with services like:
    // - AWS Rekognition
    // - Azure Face API
    // - Google Cloud Vision API
    // - face-api.js library
    
    // Simple demo comparison
    return new Promise((resolve) => {
        // Simulate processing time
        setTimeout(() => {
            const similarity = Math.random() * 0.4 + 0.6; // Random between 0.6-1.0
            resolve(similarity);
        }, 1500);
    });
}

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
});

// Start server
app.listen(PORT, async () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
    await testConnection();
    
    console.log('\n📊 To view your data:');
    console.log(`1. Browser: http://localhost:${PORT}`);
    console.log(`2. API: http://localhost:${PORT}/api/users`);
    console.log('3. MySQL Workbench or phpMyAdmin');
    console.log('4. Server console logs\n');
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🔄 Shutting down gracefully...');
    await pool.end();
    process.exit(0);
});