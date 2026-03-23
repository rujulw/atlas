import { type FormEvent, type ReactElement, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import PublicPageFrame from "../components/PublicPageFrame";
import { register } from "../lib/api";

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

export default function Register(): ReactElement {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        email,
        password,
        full_name: fullName || undefined
      });
      setSuccess("registration succeeded. your account is ready for login.");
      setPassword("");
      setConfirmPassword("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "registration failed.");
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
            <p className="text-sm font-medium lowercase text-sky-200">register</p>
            <h1 className="mt-4 max-w-[11ch] text-[clamp(2.5rem,5vw,4.6rem)] leading-[0.92] font-semibold tracking-[-0.065em] text-white">
              build your atlas identity.
            </h1>
            <p className="mt-5 max-w-xl text-[1rem] leading-7 text-slate-400">
              Atlas handles the account layer first so future apps can inherit identity, sessions, and trust without
              duplicating auth.
            </p>

            <div className="mt-8 grid gap-4 md:grid-cols-2">
              <div className="border-t border-white/8 pt-5">
                <p className="text-sm font-medium lowercase text-sky-200">owner context</p>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  Register once, then use the same identity boundary across owner-scoped storage and future private
                  services.
                </p>
              </div>
              <div className="border-t border-white/8 pt-5">
                <p className="text-sm font-medium lowercase text-sky-200">session model</p>
                <p className="mt-3 text-sm leading-7 text-slate-400">
                  Atlas is designed around rotating sessions and short-lived access tokens instead of long-lived browser
                  trust.
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
                to="/login"
                className="inline-flex items-center justify-center rounded-2xl px-2 py-2 text-sm font-medium text-slate-300 transition duration-200 hover:text-white"
              >
                Already have an account? Log in
              </Link>
            </div>
          </div>

          <div className="rounded-4xl border border-white/9 bg-black/50 p-6 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur-sm md:p-8">
            <p className="text-sm font-medium lowercase text-sky-200">create account</p>
            <h2 className="mt-4 text-[1.85rem] leading-[1.02] font-semibold tracking-[-0.055em] text-white">
              register for your private cloud.
            </h2>

            <form className="mt-6 grid gap-4 border-t border-white/8 pt-5" onSubmit={handleSubmit}>
              <label className="grid gap-2 text-sm text-slate-300">
                Username
                <input
                  className="w-[min(100%,28rem)] rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-slate-100 outline-none transition duration-200 placeholder:text-slate-500 focus:border-sky-300/45 focus:bg-white/6"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Enter username"
                  autoComplete="username"
                />
              </label>

              <label className="grid gap-2 text-sm text-slate-300">
                Email
                <input
                  className="w-[min(100%,28rem)] rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-slate-100 outline-none transition duration-200 placeholder:text-slate-500 focus:border-sky-300/45 focus:bg-white/6"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="Enter email address"
                  autoComplete="email"
                  type="email"
                  required
                />
              </label>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="grid gap-2 text-sm text-slate-300">
                  Password
                  <input
                    className="w-[min(100%,28rem)] rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-slate-100 outline-none transition duration-200 placeholder:text-slate-500 focus:border-sky-300/45 focus:bg-white/6"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Create password"
                    autoComplete="new-password"
                    type="password"
                    required
                  />
                </label>

                <label className="grid gap-2 text-sm text-slate-300">
                  Confirm password
                  <input
                    className="w-[min(100%,28rem)] rounded-2xl border border-white/10 bg-white/4 px-4 py-3 text-slate-100 outline-none transition duration-200 placeholder:text-slate-500 focus:border-sky-300/45 focus:bg-white/6"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    placeholder="Repeat password"
                    autoComplete="new-password"
                    type="password"
                    required
                  />
                </label>
              </div>

              {error ? <p className="text-sm text-rose-200">{error}</p> : null}

              {success ? <p className="text-sm text-emerald-200">{success}</p> : null}

              <div className="h-3" />

              <button
                type="submit"
                disabled={isSubmitting}
                className="mx-auto inline-flex min-w-36 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#b6f6ff_0%,#76e2ff_40%,#9f8cff_100%)] px-5 py-2.5 text-sm font-medium text-slate-950 shadow-[0_14px_30px_rgba(107,196,255,0.18)] transition-opacity duration-200 hover:opacity-92 disabled:opacity-70"
              >
                {isSubmitting ? "creating account..." : "create atlas account"}
              </button>
            </form>
          </div>
        </motion.section>
      </div>
    </PublicPageFrame>
  );
}
