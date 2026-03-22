import { useState } from "react";
import "./App.css";
import Dashboard from "./Dashboard";

const BASE_URL = "https://cpa-backend-k600.onrender.com";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("token")
  );

  // 🔐 Safe response handler
  const handleResponse = async (res) => {
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      throw new Error(text);
    }
  };

  // 🆕 REGISTER
  const register = async () => {
    if (!email || !password) {
      alert("Email and password required ⚠️");
      return;
    }

    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await handleResponse(res);

      alert(data.message || "Registered successfully ✅");

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 🔐 LOGIN
  const login = async () => {
    if (!email || !password) {
      alert("Email and password required ⚠️");
      return;
    }

    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await handleResponse(res);

      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        setIsLoggedIn(true);
      } else {
        alert(data.detail || "Login failed ❌");
      }

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 🔥 If logged in → show dashboard
  if (isLoggedIn) {
    return <Dashboard setIsLoggedIn={setIsLoggedIn} />;
  }

  return (
    <div className="container">
      <div className="card">
        <h1>💰 Earn Money</h1>
        <p className="subtitle">Complete tasks. Earn rewards.</p>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <div className="buttons">
          <button onClick={register} disabled={loading}>
            {loading ? "Please wait..." : "Register"}
          </button>

          <button className="login" onClick={login} disabled={loading}>
            {loading ? "Please wait..." : "Login"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;