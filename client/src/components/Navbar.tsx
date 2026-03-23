import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import LiquidGlass from "./LiquidGlass";

const navItems = [
  { hash: "#top", label: "Home" },
  { hash: "#solutions", label: "Solutions" },
  { hash: "#products", label: "Products" },
  { hash: "#resources", label: "Resources" }
] as const;

export default function Navbar() {
  const [isCompact, setIsCompact] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const isLandingPage = location.pathname === "/";

  useEffect(() => {
    let previousScrollY = window.scrollY;

    function handleScroll(): void {
      const currentScrollY = window.scrollY;

      if (currentScrollY < 24) {
        setIsCompact(false);
      } else if (currentScrollY > previousScrollY + 6) {
        setIsCompact(true);
        setIsMenuOpen(false);
      } else if (currentScrollY < previousScrollY - 6) {
        setIsCompact(false);
      }

      previousScrollY = currentScrollY;
    }

    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-30 flex justify-center px-4 pt-[max(1rem,env(safe-area-inset-top))] md:px-6 md:pt-[max(1.5rem,env(safe-area-inset-top))]">
      <div className="w-full max-w-5xl">
        <LiquidGlass
          className={`mx-auto px-4 py-2 transition-[max-width,padding,transform,background-color] duration-300 ${
            isCompact ? "max-w-3xl" : "max-w-4xl"
          }`}
        >
          <div className="flex items-center justify-between gap-3">
            <a
              href={isLandingPage ? "#top" : "/"}
              className="group flex min-w-0 items-center gap-3 rounded-full px-2 py-1 text-slate-50 transition-colors hover:text-white"
            >
              <div className="grid size-9 place-items-center rounded-full bg-[linear-gradient(135deg,#9ffcff_0%,#7de7ff_42%,#b19eef_100%)] text-xs text-slate-950 shadow-[0_10px_30px_rgba(125,231,255,0.35)] transition-all duration-300">
                at
              </div>
              <div className="min-w-0 text-left">
                <p className="truncate text-[0.95rem] font-semibold tracking-[-0.04em] text-white transition-all duration-300">
                  atlas
                </p>
              </div>
            </a>

            <nav className="hidden items-center gap-1 md:flex">
              {navItems.map((item) => (
                <a
                  key={item.hash}
                  href={item.hash === "#top" ? (isLandingPage ? "#top" : "/") : isLandingPage ? item.hash : `/${item.hash}`}
                  className="px-3 py-2 text-sm font-medium text-slate-100/64 transition-colors duration-300 hover:text-white"
                >
                  {item.label}
                </a>
              ))}
            </nav>

            <div className="hidden items-center gap-2 md:flex">
              <Link
                to="/login"
                className="rounded-full border border-white/10 bg-white/[0.045] px-4 py-2 text-sm font-medium text-slate-100/84 transition-[border-color,background-color,color] duration-300 hover:border-white/18 hover:bg-white/[0.08] hover:text-white"
              >
                Log In
              </Link>
              <Link
                to="/register"
                className="rounded-full bg-[linear-gradient(135deg,#b6f6ff_0%,#76e2ff_44%,#9f8cff_100%)] px-4 py-2 text-sm font-medium text-slate-950 shadow-[0_10px_22px_rgba(107,196,255,0.2)] transition-opacity duration-300 hover:opacity-92"
              >
                Sign Up
              </Link>
            </div>

            <button
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/14 bg-white/8 text-sm font-medium text-white transition hover:bg-white/14 md:hidden"
              onClick={() => setIsMenuOpen((open) => !open)}
              aria-expanded={isMenuOpen}
              aria-label="Toggle navigation menu"
            >
              {isMenuOpen ? "Close" : "Menu"}
            </button>
          </div>

          {isMenuOpen ? (
            <div className="mt-3 border-t border-white/12 pt-3 md:hidden">
              <nav className="grid gap-2">
                {navItems.map((item) => (
                  <a
                    key={item.hash}
                    href={item.hash === "#top" ? (isLandingPage ? "#top" : "/") : isLandingPage ? item.hash : `/${item.hash}`}
                    className="rounded-2xl px-4 py-3 text-sm font-medium text-slate-100 transition hover:bg-white/10"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {item.label}
                  </a>
                ))}
                <Link
                  to="/register"
                  className="mt-1 rounded-2xl bg-[linear-gradient(135deg,#b6f6ff_0%,#76e2ff_40%,#9f8cff_100%)] px-4 py-3 text-center text-sm font-medium text-slate-950"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign Up
                </Link>
              </nav>
            </div>
          ) : null}
        </LiquidGlass>
      </div>
    </header>
  );
}
