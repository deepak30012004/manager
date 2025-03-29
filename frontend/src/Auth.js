import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

function Auth() {
  const [isLogin, setIsLogin] = useState(true); // Toggle between Login and Signup
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("staff"); // Default to 'staff' for signup
  const navigate = useNavigate();

  // Handle form submission for login or signup
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (isLogin) {
      // Login
      try {
        const response = await axios.post("http://localhost:5000/login", {
          username,
          password,
        });
        localStorage.setItem("token", response.data.token);
        localStorage.setItem("role", response.data.role); // Save the role
        alert(response.data.message);
        navigate("/visitors"); // Redirect to the Visitors page after successful login
      } catch (error) {
        alert("Invalid credentials or server error.");
        console.error("Login error", error);
      }
    } else {
      // Signup
      try {
        const response = await axios.post("http://localhost:5000/signup", {
          username,
          password,
          role,
        });
        alert(response.data.message);
        setIsLogin(true); // Switch to login after successful signup
      } catch (error) {
        alert("Signup error or username already exists.");
        console.error("Signup error", error);
      }
    }
  };

  // Toggle between Login and Signup form
  const toggleForm = () => {
    setIsLogin(!isLogin);
    setUsername(""); // Clear username and password fields
    setPassword("");
  };

  return (
    <div>
      <h2>{isLogin ? "Login" : "Signup"}</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          type="password"
          name="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        {!isLogin && (
          <select
            name="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            required
          >
            <option value="staff">Staff</option>
            <option value="manager">Manager</option>
          </select>
        )}
        <button type="submit">{isLogin ? "Login" : "Signup"}</button>
      </form>

      <button onClick={toggleForm}>
        {isLogin ? "Don't have an account? Signup" : "Already have an account? Login"}
      </button>
    </div>
  );
}

export default Auth;
