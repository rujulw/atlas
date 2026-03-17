import { type FormEvent, type ReactElement, useState } from "react";

import { fetchHealth, login, register } from "./lib/api";

function App(): ReactElement {
  const [healthStatus, setHealthStatus] = useState("idle");
  const [token, setToken] = useState("");
  const [feedback, setFeedback] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  const authState = token ? "access token issued" : "not authenticated";
  const feedbackTone = feedback.toLowerCase().includes("succeeded") ? "success" : "error";

  async function handleHealthCheck(): Promise<void> {
    setFeedback("");
    try {
      const response = await fetchHealth();
      setHealthStatus(response.status);
    } catch (requestError) {
      setHealthStatus("error");
      setFeedback(requestError instanceof Error ? requestError.message : "Unknown health check error");
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFeedback("");

    try {
      const response = await login({ email, password });
      setToken(response.access_token);
      setFeedback("Login succeeded. Atlas returned a bearer access token.");
    } catch (requestError) {
      setToken("");
      setFeedback(requestError instanceof Error ? requestError.message : "Unknown login error");
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFeedback("");

    try {
      await register({ email, password, full_name: fullName });
      setFeedback("Registration succeeded. You can now log in with the same credentials.");
    } catch (requestError) {
      setFeedback(requestError instanceof Error ? requestError.message : "Unknown register error");
    }
  }

  return (
    <main className="landing-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <div className="grid-overlay" />

      <section className="hero-frame">
        <div className="hero-grid">
          <section className="hero-copy" id="overview">
            <h1>
              atlas.
            </h1>

            <div className="hero-actions">
              <button type="button" className="primary-button" onClick={handleHealthCheck}>
                check node health
              </button>
              <a className="secondary-button" href="#auth-console">
                open auth console
              </a>
            </div>

            <dl className="stat-row">
              <div>
                <dt>health</dt>
                <dd>{healthStatus}</dd>
              </div>
              <div>
                <dt>auth</dt>
                <dd>{authState}</dd>
              </div>
              <div>
                <dt>network</dt>
                <dd>tailnet-first</dd>
              </div>
            </dl>
          </section>

          <aside className="auth-column" id="auth-console">
            <form className="auth-form" onSubmit={handleLogin}>
              <div className="form-heading">
                <p>login</p>
              </div>

              <label>
                Email
                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="user@example.com"
                />
              </label>

              <label>
                Password
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  placeholder="password"
                />
              </label>

              <button type="submit" className="primary-button form-button">
                login
              </button>
            </form>

            <form className="auth-form auth-form-secondary" onSubmit={handleRegister}>
              <div className="form-heading">
                <p>register</p>
              </div>

              <label>
                Username
                <input
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Person1"
                />
              </label>

              <button type="submit" className="secondary-button form-button">
                register
              </button>
            </form>

            {feedback ? (
              <p className={`feedback-line feedback-${feedbackTone}`}>{feedback.toLowerCase()}</p>
            ) : null}

            {token ? (
              <div className="token-panel">
                <p className="token-label">access token</p>
                <p className="token-value">{token}</p>
              </div>
            ) : null}
          </aside>
        </div>
      </section>
    </main>
  );
}

export default App;
