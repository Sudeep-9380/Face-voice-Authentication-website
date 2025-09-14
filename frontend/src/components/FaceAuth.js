import React, { useState } from "react";
import { registerFace, authenticateFace } from "../api";

function FaceAuth() {
  const [username, setUsername] = useState("");
  const [image, setImage] = useState(null);
  const [message, setMessage] = useState("");

  const handleRegister = async () => {
    if (!username || !image) {
      setMessage("Please enter username and select an image.");
      return;
    }
    const result = await registerFace(username, image);
    setMessage(result.message || "Registration response received.");
  };

  const handleAuthenticate = async () => {
    if (!image) {
      setMessage("Please select an image for authentication.");
      return;
    }
    const result = await authenticateFace(image);
    setMessage(result.message || "Authentication response received.");
  };

  return (
    <div>
      <h2>Face Authentication</h2>
      <input
        type="text"
        placeholder="Username"
        onChange={(e) => setUsername(e.target.value)}
      />
      <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} />
      <br />
      <button onClick={handleRegister}>Register Face</button>
      <button onClick={handleAuthenticate}>Authenticate Face</button>
      <p>{message}</p>
    </div>
  );
}

export default FaceAuth;
