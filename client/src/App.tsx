import { type FormEvent, type ReactElement, useMemo, useState } from "react";

import StatusCard from "./components/StatusCard";
import { fetchHealth, login, register } from "./lib/api";

function App(): ReactElement {
  const [healthStatus, setHealthStatus] = useState("idle");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");

  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("password123");
  const [fullName, setFullName] = useState("Atlas User");

  const authState = useMemo(() => (token ? "token received" : "not authenticated"), [token]);

  async function handleHealthCheck(): Promise<void> {
    setError("");
    try {
      const response = await fetchHealth();
      setHealthStatus(response.status);
    } catch (requestError) {
      setHealthStatus("error");
      setError(requestError instanceof Error ? requestError.message : "Unknown health check error");
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");

    try {
      const response = await login({ email, password });
      setToken(response.access_token);
    } catch (requestError) {
      setToken("");
      setError(requestError instanceof Error ? requestError.message : "Unknown login error");
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");

    try {
      await register({ email, password, full_name: fullName });
      setError("register endpoint reached (expected 501 until implemented)");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown register error");
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">Atlas</p>
        <h1>Client Integration</h1>
        <p>
          Frontend is connected to backend stubs for health and authentication APIs.
        </p>
        <div className="status-grid">
          <StatusCard label="Health" value={healthStatus} tone={healthStatus === "ok" ? "success" : "default"} />
          <StatusCard label="Auth" value={authState} tone={token ? "success" : "default"} />
        </div>
        <button type="button" onClick={handleHealthCheck}>
          Run health check
        </button>
      </section>

      <section className="panel muted">
        <h2>Auth Stubs</h2>
        <form className="form-grid" onSubmit={handleLogin}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
          </label>
          <button type="submit">Login</button>
        </form>

        <form className="form-grid" onSubmit={handleRegister}>
          <label>
            Full name
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
          </label>
          <button type="submit">Try register</button>
        </form>

        {token ? <p className="token-line">Access token: {token}</p> : null}
        {error ? <p className="error-line">{error}</p> : null}
      </section>
    </main>
  );
}

export default App;
