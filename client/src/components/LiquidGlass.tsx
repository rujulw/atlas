import { type HTMLAttributes } from "react";

type LiquidGlassProps = HTMLAttributes<HTMLDivElement>;

export default function LiquidGlass({ children, className = "", ...props }: LiquidGlassProps) {
  return (
    <div
      className={`relative rounded-full border border-white/12 bg-white/[0.075] shadow-[0_14px_50px_rgba(4,9,21,0.24),inset_0_1px_0_rgba(255,255,255,0.18),inset_0_-1px_0_rgba(255,255,255,0.04)] backdrop-blur-xl ${className}`}
      {...props}
    >
      <div className="absolute inset-0 overflow-hidden rounded-full">
        <div className="pointer-events-none absolute left-5 top-2 h-8 w-20 rounded-full bg-white/8 blur-xl" />
        <div className="pointer-events-none absolute -right-6 bottom-0 h-12 w-20 rounded-full bg-cyan-200/8 blur-2xl" />
        <div className="pointer-events-none absolute inset-[1px] rounded-full bg-[linear-gradient(180deg,rgba(255,255,255,0.09),rgba(255,255,255,0.025)_35%,rgba(255,255,255,0.015)_100%)]" />
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}
