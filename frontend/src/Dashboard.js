import { useEffect, useState, useCallback } from "react";
import "./App.css";

const BASE_URL = "https://cpa-backend-k600.onrender.com";

function Dashboard({ setIsLoggedIn }) {
  const [balance, setBalance] = useState(0);
  const [link, setLink] = useState("");
  const [transactions, setTransactions] = useState([]);

  // 💸 Withdrawal state
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("upi");
  const [account, setAccount] = useState("");

  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem("token");

  // 🔐 Logout
  const logout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
  };

  // 🔐 Safe response handler
  const handleResponse = async (res) => {
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      throw new Error(text);
    }
  };

  // 💰 Get Balance (FIXED with useCallback ✅)
  const fetchBalance = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/wallet/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await handleResponse(res);
      setBalance(data.balance || 0);
    } catch (err) {
      console.error("Balance error:", err.message);
    }
  }, [token]);

  // 📊 Transactions (FIXED ✅)
  const fetchTransactions = useCallback(async () => {
    try {
      const res = await fetch(`${BASE_URL}/wallet/transactions`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await handleResponse(res);
      setTransactions(data.transactions || []);
    } catch (err) {
      console.error("Transaction error:", err.message);
    }
  }, [token]);

  // 🔗 Generate Link
  const generateLink = async () => {
    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/wallet/generate-link`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await handleResponse(res);

      if (data.offer_link) {
        setLink(data.offer_link);
      } else {
        alert(data.detail || "Error generating link");
      }

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 💸 Withdraw
  const withdraw = async () => {
    if (!amount || !account) {
      alert("Enter all details ⚠️");
      return;
    }

    if (amount < 100) {
      alert("Minimum withdrawal is ₹100 ⚠️");
      return;
    }

    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/wallet/withdraw`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: parseFloat(amount),
          method,
          account
        })
      });

      const data = await handleResponse(res);

      alert(data.message || data.detail || "Request sent");

      // reset form
      setAmount("");
      setAccount("");

      // refresh data
      fetchBalance();
      fetchTransactions();

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 🔄 Auto refresh (NO WARNING NOW ✅)
  useEffect(() => {
    fetchBalance();
    fetchTransactions();

    const interval = setInterval(() => {
      fetchBalance();
      fetchTransactions();
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchBalance, fetchTransactions]);

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

      {/* ACTION */}
      <div className="actions">
        <button onClick={generateLink} disabled={loading}>
          {loading ? "Please wait..." : "🎯 Generate Link"}
        </button>
      </div>

      {/* LINK */}
      {link && (
        <div className="offer">
          <a href={link} target="_blank" rel="noreferrer">
            <button>Start Earning 💰</button>
          </a>
        </div>
      )}

      {/* 💸 WITHDRAW */}
      <div className="withdraw-box">
        <h3>💸 Withdraw</h3>

        <input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />

        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="upi">UPI</option>
          <option value="paytm">Paytm</option>
          <option value="bank">Bank</option>
        </select>

        <input
          type="text"
          placeholder="UPI ID / Account"
          value={account}
          onChange={(e) => setAccount(e.target.value)}
        />

        <button onClick={withdraw} disabled={loading}>
          {loading ? "Processing..." : "Withdraw"}
        </button>
      </div>

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