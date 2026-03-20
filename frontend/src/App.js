import { useState } from "react";

const API = "http://127.0.0.1:8000";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [balance, setBalance] = useState(0);
  const [userId, setUserId] = useState(0);

  // 🔐 Register
  const register = async () => {
    await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    alert("Registered successfully!");
  };

  // 🔐 Login
  const login = async () => {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    setToken(data.access_token);

    getUser(data.access_token);
    getBalance(data.access_token);
  };

  // 👤 Get user info
  const getUser = async (tk) => {
    const res = await fetch(`${API}/wallet/me`, {
      headers: { Authorization: "Bearer " + tk }
    });

    const data = await res.json();
    setUserId(data.user_id);
  };

  // 💰 Get balance
  const getBalance = async (tk) => {
    const res = await fetch(`${API}/wallet/balance`, {
      headers: { Authorization: "Bearer " + tk }
    });

    const data = await res.json();
    setBalance(data.balance);
  };

  // 🎯 REAL CPA EARN (UPDATED)
  const earn = () => {
    window.open(
      `https://singingfiles.com/show.php?l=0&u=712357&id=70069&subid=${userId}`
    );
  };

  // 💸 Withdraw
 const withdraw = async () => {
  const res = await fetch(`${API}/wallet/withdraw?amount=100`, {
    method: "POST",
    headers: { Authorization: "Bearer " + token }
  });

  const data = await res.json();

  if (res.ok) {
    alert("Withdrawal requested!");
  } else {
    alert(data.detail);
  }

  getBalance(token);
};

  return (
    <div style={container}>
      <div style={card}>
        <h1 style={{ marginBottom: "20px" }}>💰 Earn App</h1>

        {!token ? (
          <>
            <input
              placeholder="Email"
              onChange={(e) => setEmail(e.target.value)}
              style={input}
            />

            <input
              type="password"
              placeholder="Password"
              onChange={(e) => setPassword(e.target.value)}
              style={input}
            />

            <button style={btnPrimary} onClick={register}>
              Register
            </button>

            <button style={btnSecondary} onClick={login}>
              Login
            </button>
          </>
        ) : (
          <>
            <h2 style={balanceText}>₹{balance}</h2>
            <p style={{ color: "#777" }}>Available Balance</p>

            <button style={btnPrimary} onClick={earn}>
              Earn ₹50
            </button>

            <button 
  style={btnDanger} 
  onClick={withdraw}
  disabled={balance < 100}
>
  {balance >= 100 ? "Withdraw ₹100" : "Minimum ₹100 required"}
</button>
          </>
        )}
      </div>
    </div>
  );
}

// 🎨 Styles

const container = {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  height: "100vh",
  background: "#f4f6f9"
};

const card = {
  background: "white",
  padding: "30px",
  borderRadius: "12px",
  boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
  width: "320px",
  textAlign: "center"
};

const input = {
  width: "100%",
  padding: "10px",
  margin: "10px 0",
  borderRadius: "6px",
  border: "1px solid #ccc"
};

const btnPrimary = {
  width: "100%",
  padding: "10px",
  margin: "10px 0",
  background: "#3498db",
  color: "white",
  border: "none",
  borderRadius: "6px",
  cursor: "pointer"
};

const btnSecondary = {
  ...btnPrimary,
  background: "#2ecc71"
};

const btnDanger = {
  ...btnPrimary,
  background: "#e74c3c"
};

const balanceText = {
  color: "#2ecc71",
  fontSize: "28px",
  margin: "10px 0"
};

export default App;