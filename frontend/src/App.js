import React, { useState, useEffect } from 'react';

function App() {
  const [backendData, setBackendData] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch data when component mounts
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchBackendData(), fetchUsers()]);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching initial data:', err);
      setError('Failed to fetch initial data from backend.');
      setLoading(false);
    }
  };

  const fetchBackendData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/data');
      if (!response.ok) throw new Error(`Status: ${response.status}`);
      const data = await response.json();
      setBackendData(data);
    } catch (err) {
      console.error('Error fetching backend data:', err);
      setError('Failed to connect to backend.');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/users');
      if (!response.ok) throw new Error(`Status: ${response.status}`);
      const data = await response.json();
      setUsers(data.users || []);
    } catch (err) {
      console.error('Error fetching users:', err);
      setUsers([]);
    }
  };

  const addUser = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'New User',
          email: 'newuser@example.com'
        })
      });
      if (!response.ok) throw new Error(`Status: ${response.status}`);
      const result = await response.json();
      console.log('User added:', result);
      fetchUsers(); // Refresh users list
    } catch (err) {
      console.error('Error adding user:', err);
    }
  };

  if (loading) {
    return <div className="App">Loading...</div>;
  }

  if (error) {
    return (
      <div className="App">
        <h1>Connection Error</h1>
        <p>{error}</p>
        <p>Ensure your backend is running on <b>http://localhost:5000</b></p>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Full Stack Application</h1>

        {/* Backend Connection Status */}
        <div className="status-section">
          <h2>Backend Connection Status</h2>
          {backendData ? (
            <div>
              <p>✅ Successfully connected to backend!</p>
              <p>Data: {backendData.data || 'No data available'}</p>
              <p>Timestamp: {backendData.timestamp || 'N/A'}</p>
            </div>
          ) : (
            <p>❌ No data received from backend.</p>
          )}
        </div>

        {/* Users Section */}
        <div className="users-section">
          <h2>Users from Backend</h2>
          <button
            onClick={addUser}
            style={{ marginBottom: '20px', padding: '10px 20px' }}
          >
            Add New User
          </button>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {users.length > 0 ? (
              users.map(user => (
                <li
                  key={user.id || user._id}
                  style={{
                    margin: '10px 0',
                    padding: '10px',
                    border: '1px solid #ccc',
                    borderRadius: '5px'
                  }}
                >
                  <strong>{user.name}</strong> - {user.email}
                </li>
              ))
            ) : (
              <li>No users found</li>
            )}
          </ul>
        </div>

        {/* API Testing Section */}
        <div className="api-section">
          <h2>Test Backend APIs</h2>
          <button onClick={fetchBackendData} style={{ margin: '5px', padding: '10px 20px' }}>
            Refresh Data
          </button>
          <button onClick={fetchUsers} style={{ margin: '5px', padding: '10px 20px' }}>
            Refresh Users
          </button>
        </div>
      </header>
    </div>
  );
}

export default App;
