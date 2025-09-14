const API_BASE = "http://127.0.0.1:5000/api"; // Change if needed

export async function registerFace(username, imageFile) {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("image", imageFile);

  const response = await fetch(`${API_BASE}/register-face`, {
    method: "POST",
    body: formData,
  });
  return response.json();
}

export async function authenticateFace(imageFile) {
  const formData = new FormData();
  formData.append("image", imageFile);

  const response = await fetch(`${API_BASE}/authenticate-face`, {
    method: "POST",
    body: formData,
  });
  return response.json();
}

// Similarly, add registerVoice() and authenticateVoice()
