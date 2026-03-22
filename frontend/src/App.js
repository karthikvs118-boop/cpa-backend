import { useState } from "react";

const BASE_URL = "https://cpa-backend-k600.onrender.com";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [balance, setBalance] = useState(0);
  const [taskLink, setTaskLink] = useState("");

  const register = async () => {
    await fetch(`${BASE_URL}/auth/register`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ email, password })
    });
    alert("Registered ✅");
  };

  const login = async () => {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    setToken(data.access_token);
    getBalance(data.access_token);
  };

  const getBalance = async (tok = token) => {
    const res = await fetch(`${BASE_URL}/wallet/balance`, {
      headers: { Authorization: "Bearer " + tok }
    });
    const data = await res.json();
    setBalance(data.balance);
  };

  const getTask = async () => {
    const res = await fetch(`${BASE_URL}/wallet/generate-link`, {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();
    setTaskLink(data.offer_link);
  };

  const withdraw = async () => {
    const amount = prompt("Enter amount");

    await fetch(`${BASE_URL}/wallet/withdraw?amount=${amount}`, {
      method: "POST",
      headers: { Authorization: "Bearer " + token }
    });

    alert("Withdrawal requested 💸");
    getBalance();
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>

        <h1 style={styles.title}>💰 Earn Money</h1>

        {!token ? (
          <>
            <input
              style={styles.input}
              placeholder="Email"
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              style={styles.input}
              type="password"
              placeholder="Password"
              onChange={(e) => setPassword(e.target.value)}
            />

            <button style={styles.primaryBtn} onClick={register}>
              Register
            </button>

            <button style={styles.secondaryBtn} onClick={login}>
              Login
            </button>
          </>
        ) : (
          <>
            <h2 style={styles.balance}>₹{balance}</h2>

            <button style={styles.primaryBtn} onClick={getTask}>
              🎯 Get Task
            </button>

            <button style={styles.secondaryBtn} onClick={getBalance}>
              🔄 Refresh
            </button>

            {taskLink && (
              <a href={taskLink} target="_blank" rel="noreferrer">
                <button style={styles.taskBtn}>🚀 Start Task</button>
              </a>
            )}

            <button style={styles.withdrawBtn} onClick={withdraw}>
              💸 Withdraw
            </button>
          </>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    background: "linear-gradient(135deg, #0f172a, #1e293b)"
  },
  card: {
    background: "#1e293b",
    padding: "30px",
    borderRadius: "15px",
    width: "320px",
    textAlign: "center",
    boxShadow: "0 10px 30px rgba(0,0,0,0.5)"
  },
  title: {
    marginBottom: "20px"
  },
  input: {
    width: "100%",
    padding: "12px",
    marginBottom: "10px",
    borderRadius: "8px",
    border: "none",
    outline: "none"
  },
  primaryBtn: {
    width: "100%",
    padding: "12px",
    marginTop: "10px",
    borderRadius: "8px",
    border: "none",
    background: "#22c55e",
    color: "white",
    fontWeight: "bold",
    cursor: "pointer"
  },
  secondaryBtn: {
    width: "100%",
    padding: "12px",
    marginTop: "10px",
    borderRadius: "8px",
    border: "none",
    background: "#334155",
    color: "white",
    cursor: "pointer"
  },
  taskBtn: {
    width: "100%",
    padding: "12px",
    marginTop: "15px",
    borderRadius: "8px",
    border: "none",
    background: "#3b82f6",
    color: "white",
    fontWeight: "bold",
    cursor: "pointer"
  },
  withdrawBtn: {
    width: "100%",
    padding: "12px",
    marginTop: "15px",
    borderRadius: "8px",
    border: "none",
    background: "#ef4444",
    color: "white",
    fontWeight: "bold",
    cursor: "pointer"
  },
  balance: {
    marginBottom: "15px"
  }
};

export default App;