import { type FormEvent, type ReactElement, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import PublicPageFrame from "../components/PublicPageFrame";
import { login } from "../lib/api";

const sectionReveal = {
  hidden: { opacity: 0, y: 28, filter: "blur(10px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: {
      duration: 0.75,
      ease: [0.22, 1, 0.36, 1]
    }
  }
} as const;

export default function Login(): ReactElement {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");
    setToken("");
    setIsSubmitting(true);

    try {
      const response = await login({ email, password });
      setToken(response.access_token);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PublicPageFrame compact>
      <div className="flex justify-center">
        <motion.section
          className="grid min-h-[calc(100svh-8rem)] w-full max-w-6xl gap-5 py-4 md:min-h-[calc(100svh-9rem)] md:py-6 lg:grid-cols-[1fr_0.88fr] lg:items-center"
          initial="hidden"
          animate="visible"
          variants={sectionReveal}
        >
          <div className="px-3 py-6 md:px-6">
            <p className="text-sm font-medium lowercase text-sky-200">login</p>
            <h1 className="mt-4 max-w-[10ch] text-[clamp(2.5rem,5vw,4.6rem)] leading-[0.92] font-semibold tracking-[-0.065em] text-white">
              return to atlas.
            </h1>
            <p className="mt-5 max-w-xl text-[1rem] leading-7 text-slate-400">
              Sign in to continue into your private Atlas environment.
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <div className="border-t border-white/8 pt-5">
                <p className="text-sm font-medium lowercase text-sky-200">short-lived access</p>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  Atlas issues bearer access tokens while tracking longer-lived sessions separately.
                </p>
              </div>
              <div className="border-t border-white/8 pt-5">
                <p className="text-sm font-medium lowercase text-sky-200">future app shell</p>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  The next client slice will consume this auth layer inside the protected `/app` route.
                </p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to="/"
                className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/4 px-5 py-3 text-sm font-medium text-slate-200/88 transition duration-200 hover:border-white/16 hover:bg-white/6 hover:text-white"
              >
                Back home
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center justify-center rounded-2xl px-2 py-2 text-sm font-medium text-slate-300 transition duration-200 hover:text-white"
              >
                Need an account? Sign up
              </Link>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/9 bg-black/50 p-6 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur-sm md:p-8">
            <p className="text-sm font-medium lowercase text-sky-200">access session</p>
            <h2 className="mt-4 text-[1.85rem] leading-[1.02] font-semibold tracking-[-0.055em] text-white">
              log in to your private cloud.
            </h2>

            <form className="mt-6 grid gap-4 border-t border-white/8 pt-5" onSubmit={handleSubmit}>
              <label className="grid gap-2 text-sm text-slate-300">
                Email
                <input
                  className="w-[min(100%,28rem)] rounded-[1rem] border border-white/10 bg-white/4 px-4 py-3 text-slate-100 outline-none transition duration-200 placeholder:text-slate-500 focus:border-sky-300/45 focus:bg-white/6"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="Enter email address"
                  autoComplete="email"
                  type="email"
                  required
                />
              </label>

              <label className="grid gap-2 text-sm text-slate-300">
                Password
                <input
                  className="w-[min(100%,28rem)] rounded-[1rem] border border-white/10 bg-white/4 px-4 py-3 text-slate-100 outline-none transition duration-200 placeholder:text-slate-500 focus:border-sky-300/45 focus:bg-white/6"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter password"
                  autoComplete="current-password"
                  type="password"
                  required
                />
              </label>

              {error ? <p className="text-sm text-rose-200">{error}</p> : null}

              {token ? (
                <div className="border-t border-white/8 pt-4">
                  <p className="text-sm text-emerald-200">login succeeded. access token issued.</p>
                  <p className="mt-2 break-all text-xs leading-5 text-emerald-50/92">{token}</p>
                </div>
              ) : null}

              <div className="h-3" />

              <button
                type="submit"
                disabled={isSubmitting}
                className="mx-auto inline-flex min-w-36 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#b6f6ff_0%,#76e2ff_40%,#9f8cff_100%)] px-5 py-2.5 text-sm font-medium text-slate-950 shadow-[0_14px_30px_rgba(107,196,255,0.18)] transition-opacity duration-200 hover:opacity-92 disabled:opacity-70"
              >
                {isSubmitting ? "logging in..." : "log in"}
              </button>
            </form>
          </div>
        </motion.section>
      </div>
    </PublicPageFrame>
  );
}
