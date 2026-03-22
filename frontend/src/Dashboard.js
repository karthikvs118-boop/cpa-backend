import { useEffect, useState } from "react";
import "./App.css";

const BASE_URL = "https://cpa-backend-k600.onrender.com";

function Dashboard({ setIsLoggedIn }) {
  const [balance, setBalance] = useState(0);
  const [link, setLink] = useState("");
  const [transactions, setTransactions] = useState([]);

  const token = localStorage.getItem("token");

  // 🔐 Logout
  const logout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
  };

  // 💰 Get Balance
  const fetchBalance = async () => {
    const res = await fetch(`${BASE_URL}/wallet/balance`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const data = await res.json();
    setBalance(data.balance || 0);
  };

  // 🔗 Generate CPA Link
  const generateLink = async () => {
    const res = await fetch(`${BASE_URL}/wallet/generate-link`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const data = await res.json();

    if (data.link) {
      setLink(data.link);
    } else {
      alert(data.detail || "Error generating link");
    }
  };

  // 📊 Get Transactions
  const fetchTransactions = async () => {
    const res = await fetch(`${BASE_URL}/wallet/transactions`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const data = await res.json();
    setTransactions(data.transactions || []);
  };

  // 🚀 Load on start
  useEffect(() => {
    fetchBalance();
    fetchTransactions();
  }, []);

  return (
    <div className="dashboard">
      
      {/* HEADER */}
      <div className="navbar">
        <h2>💰 Easy Earnings</h2>
        <button onClick={logout}>Logout</button>
      </div>

      {/* BALANCE */}
      <div className="balance-card">
        <h3>Your Balance</h3>
        <h1>₹{balance}</h1>
      </div>

      {/* ACTIONS */}
      <div className="actions">
        <button onClick={generateLink}>🎯 Generate Link</button>
      </div>

      {/* LINK DISPLAY */}
      {link && (
        <div className="offer">
          <p>{link}</p>
        </div>
      )}

      {/* TRANSACTIONS */}
      <div className="offers">
        <h3>📊 Transactions</h3>

        {transactions.length === 0 ? (
          <p>No transactions yet</p>
        ) : (
          transactions.map((t, i) => (
            <div className="offer" key={i}>
              <p>{t.type}</p>
              <span>₹{t.amount}</span>
            </div>
          ))
        )}
      </div>

    </div>
  );
}

export default Dashboard;