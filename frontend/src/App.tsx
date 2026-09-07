import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(`Backend says: ${data.status}`))
      .catch(() => setStatus("Could not reach backend"));
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-slate-800">Inventory System</h1>
        <p className="mt-2 text-slate-500">{status}</p>
      </div>
    </div>
  );
}

export default App;