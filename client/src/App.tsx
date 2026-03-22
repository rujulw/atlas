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
  const feedbackTone = feedback.toLowerCase().includes("succeeded")
    ? "border-emerald-400/30 bg-emerald-400/14 text-emerald-100"
    : "border-rose-300/30 bg-rose-300/14 text-rose-100";

  const primaryButtonClassName =
    "inline-flex items-center justify-center rounded-full border border-transparent bg-[linear-gradient(135deg,#b6f6ff_0%,#76e2ff_40%,#9f8cff_100%)] px-5 py-3 text-sm font-medium text-slate-950 shadow-[0_18px_40px_rgba(107,196,255,0.2)] transition duration-150 hover:-translate-y-0.5 hover:shadow-[0_22px_46px_rgba(107,196,255,0.28)]";
  const secondaryButtonClassName =
    "inline-flex items-center justify-center rounded-full border border-white/12 bg-white/4 px-5 py-3 text-sm font-medium text-slate-100 transition duration-150 hover:-translate-y-0.5 hover:border-white/25";
  const statCardClassName =
    "rounded-[1.2rem] border border-white/6 bg-white/[0.035] p-4 text-left";
  const formClassName =
    "grid w-full max-w-[360px] gap-4 rounded-[1.6rem] border border-white/6 p-4 backdrop-blur-[18px]";
  const labelClassName = "grid gap-2 text-[0.92rem] text-slate-100";
  const inputClassName =
    "w-full rounded-[0.95rem] border border-white/12 bg-white/5 px-4 py-3 text-slate-100 outline-none transition duration-150 placeholder:text-slate-400 focus:border-cyan-300/55 focus:bg-white/7 focus:ring-4 focus:ring-cyan-300/12";
  const eyebrowClassName =
    "m-0 font-['Space_Grotesk',sans-serif] text-[0.78rem] font-semibold lowercase tracking-[0.08em] text-slate-400";

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
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden">
      <div className="absolute -left-28 -top-32 size-96 rounded-full bg-[radial-gradient(circle,rgba(154,137,255,0.24),transparent_68%)] opacity-75 blur-[20px]" />
      <div className="absolute -bottom-36 -right-28 h-[28rem] w-[28rem] rounded-full bg-[radial-gradient(circle,rgba(105,217,255,0.18),transparent_70%)] opacity-75 blur-[20px]" />
      <div className="absolute inset-0 opacity-[0.22] [background-image:linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.045)_1px,transparent_1px)] [background-size:72px_72px] [mask-image:radial-gradient(circle_at_center,black_42%,transparent_100%)]" />

      <section className="relative z-10 mx-auto w-[min(1220px,calc(100vw-1rem))] py-6 md:w-[min(1220px,calc(100vw-2rem))] md:py-8">
        <div className="grid items-center justify-center gap-6 lg:grid-cols-[minmax(0,1.08fr)_minmax(350px,0.92fr)]">
          <section className="grid justify-items-center py-6 text-center md:py-10" id="overview">
            <h1 className="mt-5 max-w-[12ch] text-[clamp(3rem,6vw,5.8rem)] leading-[0.94] font-semibold tracking-[-0.055em] md:max-w-[10.5ch]">
              atlas.
            </h1>

            <div className="mt-6 flex flex-wrap justify-center gap-4">
              <button type="button" className={primaryButtonClassName} onClick={handleHealthCheck}>
                check node health
              </button>
              <a className={secondaryButtonClassName} href="#auth-console">
                open auth console
              </a>
            </div>

            <dl className="mt-10 grid grid-cols-1 justify-center gap-3 sm:grid-cols-[repeat(3,minmax(160px,210px))]">
              <div className={statCardClassName}>
                <dt className={`${eyebrowClassName} text-left`}>health</dt>
                <dd className="mt-2 text-base text-slate-100">{healthStatus}</dd>
              </div>
              <div className={statCardClassName}>
                <dt className={`${eyebrowClassName} text-left`}>auth</dt>
                <dd className="mt-2 text-base text-slate-100">{authState}</dd>
              </div>
              <div className={statCardClassName}>
                <dt className={`${eyebrowClassName} text-left`}>network</dt>
                <dd className="mt-2 text-base text-slate-100">tailnet-first</dd>
              </div>
            </dl>
          </section>

          <aside className="relative z-10 grid justify-items-center gap-4" id="auth-console">
            <form
              className={`${formClassName} bg-[linear-gradient(180deg,rgba(11,17,32,0.96),rgba(7,11,21,0.92))] shadow-[0_28px_80px_rgba(0,0,0,0.45)]`}
              onSubmit={handleLogin}
            >
              <div className="flex items-center justify-center">
                <p className={`${eyebrowClassName} text-center text-slate-400`}>login</p>
              </div>

              <label className={labelClassName}>
                Email
                <input
                  className={inputClassName}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="user@example.com"
                />
              </label>

              <label className={labelClassName}>
                Password
                <input
                  className={inputClassName}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  placeholder="password"
                />
              </label>

              <button type="submit" className={`${primaryButtonClassName} w-full`}>
                login
              </button>
            </form>

            <form className={`${formClassName} bg-white/[0.025]`} onSubmit={handleRegister}>
              <div className="flex items-center justify-center">
                <p className={`${eyebrowClassName} text-center text-slate-400`}>register</p>
              </div>

              <label className={labelClassName}>
                Username
                <input
                  className={inputClassName}
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Person1"
                />
              </label>

              <button type="submit" className={`${secondaryButtonClassName} w-full`}>
                register
              </button>
            </form>

            {feedback ? (
              <p
                className={`relative z-10 mt-4 w-full max-w-[360px] rounded-2xl border px-4 py-3.5 leading-[1.6] ${feedbackTone}`}
              >
                {feedback.toLowerCase()}
              </p>
            ) : null}

            {token ? (
              <div className="relative z-10 mt-4 w-full max-w-[360px] rounded-[1.2rem] border border-white/6 bg-white/[0.035] p-4">
                <p className={`${eyebrowClassName} text-left`}>access token</p>
                <p className="mt-3 overflow-wrap-anywhere text-[0.88rem] leading-[1.7] text-slate-100">
                  {token}
                </p>
              </div>
            ) : null}
          </aside>
        </div>
      </section>
    </main>
  );
}

export default App;
