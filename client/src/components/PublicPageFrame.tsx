import { type ReactNode } from "react";

import Aurora from "./Aurora";
import Navbar from "./Navbar";

type PublicPageFrameProps = {
  children: ReactNode;
  compact?: boolean;
};

export default function PublicPageFrame({ children, compact = false }: PublicPageFrameProps) {
  return (
    <main className="relative min-h-screen overflow-hidden" id="top">
      <Navbar />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,#06111d_0%,#07111b_38%,#050c16_100%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-size-[72px_72px] opacity-[0.08]" />
      <div className="absolute inset-x-0 top-0 h-124 overflow-hidden opacity-52 mask-[linear-gradient(180deg,black_0%,black_70%,transparent_100%)]">
        <Aurora
          colorStops={["#4f9d8f", "#3f7f95", "#244c63"]}
          blend={0.28}
          amplitude={0.64}
          speed={0.74}
        />
      </div>

      <section
        className={`relative z-10 mx-auto w-[min(1220px,calc(100vw-1rem))] px-0 ${
          compact
            ? "pt-28 pb-8 md:w-[min(1220px,calc(100vw-2rem))] md:pt-32 md:pb-10"
            : "pt-32 pb-10 md:w-[min(1220px,calc(100vw-2rem))] md:pt-40 md:pb-16"
        }`}
      >
        {children}
      </section>
    </main>
  );
}
