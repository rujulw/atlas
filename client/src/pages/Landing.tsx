import { type ReactElement } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import Aurora from "../components/Aurora";
import Navbar from "../components/Navbar";

const featureHighlights = [
  {
    title: "Owner-scoped storage",
    body: "Every file flow is scoped to the authenticated owner, from upload through download."
  },
  {
    title: "Metadata-first search",
    body: "Browse recent files, sort predictably, and filter by filename, MIME type, size, and time windows."
  },
  {
    title: "Session-aware auth",
    body: "Atlas issues rotating sessions and short-lived access tokens with device visibility built into the model."
  }
] as const;

const productPillars = [
  {
    eyebrow: "Store",
    title: "Keep file data on hardware you control",
    body: "Atlas separates file data from metadata so storage stays efficient while ownership and lifecycle stay explicit."
  },
  {
    eyebrow: "Manage",
    title: "Browse files with stable, honest primitives",
    body: "The current storage model focuses on real capabilities: upload, list, search, metadata filters, and owner-scoped download."
  },
  {
    eyebrow: "Trust",
    title: "Use Atlas as the identity core for private apps",
    body: "The platform direction goes beyond storage: atlas becomes the account, session, and trust layer for future self-hosted services."
  }
] as const;

const resourceBlocks = [
  {
    label: "Architecture",
    title: "Private by network design",
    body: "Atlas is built around tailnet-only reachability, local-first deployment, and modular service boundaries.",
    href: "/docs"
  },
  {
    label: "API surface",
    title: "Built on stable backend contracts",
    body: "Storage listing, search, pagination, session handling, and file metadata are already shaping the client around real APIs.",
    href: "/docs"
  },
  {
    label: "Roadmap",
    title: "Growing from storage core to private platform",
    body: "The next steps move from the storage shell into richer browse flows, trusted internal services, and future media-oriented apps.",
    href: "/docs"
  }
] as const;

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

const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.08
    }
  }
} as const;

const cardReveal = {
  hidden: { opacity: 0, y: 22, scale: 0.985, filter: "blur(8px)" },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: "blur(0px)",
    transition: {
      duration: 0.65,
      ease: [0.22, 1, 0.36, 1]
    }
  }
} as const;

export default function Landing(): ReactElement {
  return (
    <main className="relative min-h-[140vh] overflow-hidden" id="top">
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

      <section className="relative z-10 mx-auto w-[min(1220px,calc(100vw-1rem))] px-0 pt-32 pb-10 md:w-[min(1220px,calc(100vw-2rem))] md:pt-40 md:pb-16">
        <div className="flex justify-center">
          <motion.section
            className="relative grid w-full max-w-5xl justify-items-center py-10 text-center md:py-16"
            id="overview"
            initial="hidden"
            animate="visible"
            variants={sectionReveal}
          >
            <h1 className="mt-10 max-w-[22ch] text-[clamp(3.15rem,6.2vw,5.7rem)] leading-[0.9] font-semibold tracking-[-0.068em] text-white [text-shadow:0_1px_0_rgba(255,255,255,0.06)] md:max-w-[18ch]">
              Private storage on hardware <span className="underline decoration-emerald-300/55 underline-offset-[0.16em]">you</span>{" "}
              control.
            </h1>
            <p className="mt-6 max-w-3xl text-[1.06rem] leading-8 text-slate-400 md:text-[1.12rem]">
              atlas keeps your files owner-scoped, self-hosted, and reachable only through the private network you trust.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/docs"
                className="inline-flex items-center justify-center rounded-full bg-[linear-gradient(135deg,#b6f6ff_0%,#76e2ff_40%,#9f8cff_100%)] px-5 py-3 text-sm font-medium text-slate-950 shadow-[0_14px_30px_rgba(107,196,255,0.18)] transition-opacity duration-200 hover:opacity-92"
              >
                Read the docs
              </Link>
              <a
                href="#products"
                className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/4 px-5 py-3 text-sm font-medium text-slate-200/88 transition duration-200 hover:border-white/16 hover:bg-white/6 hover:text-white"
              >
                Explore the platform
              </a>
            </div>
          </motion.section>
        </div>

        <motion.section
          className="mt-10 scroll-mt-28 md:mt-14 md:scroll-mt-32"
          id="solutions"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={sectionReveal}
        >
          <motion.div className="grid gap-4 lg:grid-cols-3" variants={staggerContainer}>
            {featureHighlights.map((item, index) => (
              <motion.article
                key={item.title}
                className="rounded-[1.9rem] border border-white/9 bg-black/55 p-6 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur-sm md:p-7"
                variants={cardReveal}
              >
                <div className="mb-10 h-40 overflow-hidden rounded-[1.55rem] bg-[linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] p-4">
                  {index === 0 ? (
                    <div className="flex h-full flex-col">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium lowercase text-slate-200">storage policy</p>
                        </div>
                        <div className="text-xs font-medium lowercase text-emerald-200/80">
                          enforced
                        </div>
                      </div>
                      <div className="mt-4 space-y-2">
                        {[
                          { name: "media/raw/photo-1842.heic", owner: "rujul", tint: "bg-emerald-400" },
                          { name: "contracts/vendor-q2.pdf", owner: "rujul", tint: "bg-sky-400" }
                        ].map((row) => (
                          <div key={row.name} className="flex items-center gap-3 px-1 py-1.5">
                            <div className={`h-8 w-8 rounded-lg ${row.tint} shadow-[0_8px_20px_rgba(15,23,42,0.35)]`} />
                            <div className="min-w-0 flex-1">
                              <p className="truncate text-sm text-slate-200">{row.name}</p>
                              <p className="mt-1 text-xs text-slate-500">owner={row.owner}</p>
                            </div>
                            <div className="rounded-full bg-white/5 px-2.5 py-1 text-[0.68rem] text-slate-400">
                              scoped
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : index === 1 ? (
                    <div className="flex h-full flex-col">
                      <div>
                        <p className="text-sm font-medium lowercase text-slate-200">search</p>
                        <div className="mt-2 inline-flex h-9 items-center rounded-full bg-white/4 px-4 text-sm text-slate-300">
                          filename:invoice mime:pdf last:30d
                        </div>
                      </div>
                      <div className="mt-4 grid flex-1 grid-cols-[1fr_auto] gap-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span>recent results</span>
                            <span>24 matches</span>
                          </div>
                          {["invoice-april.pdf", "invoice-march.pdf"].map((name) => (
                            <div key={name} className="px-1 py-1">
                              <p className="truncate text-sm text-slate-200">{name}</p>
                              <p className="mt-1 text-xs text-slate-500">PDF • 128 KB</p>
                            </div>
                          ))}
                        </div>
                        <div className="flex flex-col gap-2 pt-7">
                          {["MIME", "Size", "Owner"].map((label) => (
                            <div key={label} className="rounded-full bg-white/4 px-3 py-2 text-sm text-slate-300">
                              {label}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex h-full flex-col">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium lowercase text-slate-200">access control</p>
                        </div>
                        <div className="text-xs font-medium lowercase text-sky-200/80">
                          rotating
                        </div>
                      </div>
                      <div className="mt-3 grid flex-1 grid-cols-[1.15fr_0.85fr] gap-3">
                        <div className="rounded-[1.2rem] bg-[linear-gradient(135deg,rgba(39,211,220,0.9),rgba(122,167,223,0.82))] p-3 text-slate-950">
                          <p className="text-sm font-medium lowercase text-slate-950/72">access token</p>
                          <p className="mt-1.5 text-[0.95rem] font-semibold tracking-[-0.04em]">expires in 08:42</p>
                          <div className="mt-3 h-2 rounded-full bg-slate-950/10">
                            <div className="h-2 w-[68%] rounded-full bg-slate-950/70" />
                          </div>
                          <p className="mt-2 text-xs leading-4.5 text-slate-950/70">short-lived credentials</p>
                        </div>
                        <div className="space-y-1.5 pt-0.5">
                          {[
                            ["MacBook Pro", "Current device"],
                            ["iPhone", "Verified 2h ago"]
                          ].map(([device, meta]) => (
                            <div key={device} className="px-1 py-0.5">
                              <p className="text-sm text-slate-200">{device}</p>
                              <p className="mt-1 text-xs text-slate-500">{meta}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <h2 className="mt-4 text-[1.9rem] leading-none font-semibold tracking-[-0.055em] text-white lowercase">{item.title}</h2>
                <p className="mt-4 max-w-[28ch] text-[1.02rem] leading-8 text-slate-300">{item.body}</p>
              </motion.article>
            ))}
          </motion.div>

          <motion.div
            className="mt-4 scroll-mt-28 grid gap-4 lg:grid-cols-[1.95fr_0.95fr] md:scroll-mt-32"
            id="products"
            variants={staggerContainer}
          >
            <motion.article
              className="rounded-[1.9rem] border border-white/9 bg-black/55 p-6 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur-sm md:p-7"
              variants={cardReveal}
            >
              <div className="relative mb-8 overflow-hidden rounded-[1.55rem] border border-white/8 bg-[radial-gradient(circle_at_top,rgba(120,180,255,0.04),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.025),rgba(255,255,255,0.01))] p-6 md:p-7">
                <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-size-[64px_64px] opacity-25" />
                <div className="relative grid gap-5 md:grid-cols-[0.95fr_1.2fr_0.95fr] md:items-center">
                  <div className="space-y-3">
                    <div className="rounded-[1.25rem] border border-white/8 bg-black/30 p-4">
                      <p className="text-sm font-medium lowercase text-sky-200">file blobs</p>
                      <p className="mt-2 text-sm leading-6 text-slate-400">Data stays on hardware you control.</p>
                    </div>
                    <div className="rounded-[1.25rem] border border-white/8 bg-black/30 p-4">
                      <p className="text-sm font-medium lowercase text-sky-200">metadata index</p>
                      <p className="mt-2 text-sm leading-6 text-slate-400">Search, timestamps, MIME type, and ownership stay queryable.</p>
                    </div>
                  </div>

                  <div className="relative py-6">
                    <div className="mx-auto max-w-[18rem] rounded-3xl border border-slate-200/8 bg-[linear-gradient(135deg,rgba(148,163,184,0.09),rgba(71,85,105,0.03))] p-5 shadow-[0_20px_60px_rgba(15,23,42,0.16)] backdrop-blur-sm">
                      <p className="text-sm font-medium lowercase text-sky-200">atlas core</p>
                      <div className="mt-4 space-y-3">
                        {["owner-scoped storage", "session issuance", "access decisions"].map((label) => (
                          <div key={label} className="rounded-full bg-black/25 px-3 py-2 text-sm lowercase text-slate-100">
                            {label}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="absolute left-[6%] top-1/2 hidden h-px w-[28%] -translate-y-1/2 bg-[linear-gradient(90deg,rgba(255,255,255,0),rgba(148,163,184,0.35))] md:block" />
                    <div className="absolute right-[6%] top-1/2 hidden h-px w-[28%] -translate-y-1/2 bg-[linear-gradient(90deg,rgba(148,163,184,0.35),rgba(255,255,255,0))] md:block" />
                  </div>

                  <div className="space-y-3">
                    <div className="rounded-[1.25rem] border border-white/8 bg-black/30 p-4">
                      <p className="text-sm font-medium lowercase text-sky-200">private apps</p>
                      <p className="mt-2 text-sm leading-6 text-slate-400">Future services can inherit the same identity and trust boundary.</p>
                    </div>
                    <div className="rounded-[1.25rem] border border-white/8 bg-black/30 p-4">
                      <p className="text-sm font-medium lowercase text-sky-200">device sessions</p>
                      <p className="mt-2 text-sm leading-6 text-slate-400">Rotating sessions and short-lived tokens stay visible and revocable.</p>
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-sm font-medium lowercase text-sky-200">platform</p>
              <h2 className="mt-4 max-w-[18ch] text-[2.1rem] leading-[1.02] font-semibold tracking-[-0.06em] text-white lowercase">
                One storage and identity core for your private infrastructure.
              </h2>
              <p className="mt-4 max-w-4xl text-[1.02rem] leading-8 text-slate-300">
                atlas is being built as a self-hosted storage layer, an auth and session system, and a trust anchor for
                future apps that run behind the same private network boundary.
              </p>
              <div className="mt-8 grid gap-4 md:grid-cols-2">
                {productPillars.slice(0, 2).map((item) => (
                  <div key={item.title} className="rounded-[1.35rem] border border-white/8 bg-white/2 p-5">
                    <p className="text-sm font-medium lowercase text-sky-200">{item.eyebrow}</p>
                    <h3 className="mt-3 text-lg font-semibold tracking-[-0.04em] text-white lowercase">{item.title}</h3>
                    <p className="mt-3 text-sm leading-7 text-slate-400">{item.body}</p>
                  </div>
                ))}
              </div>
            </motion.article>

            <motion.article
              className="rounded-[1.9rem] border border-white/9 bg-black/55 p-6 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur-sm md:p-7"
              variants={cardReveal}
            >
              <div className="mb-8 min-h-72 rounded-[1.55rem] bg-[linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] p-4">
                <div className="flex h-full flex-col justify-between">
                  <div className="flex items-start gap-4">
                    <div className="mt-1 h-20 w-px bg-[linear-gradient(180deg,rgba(148,163,184,0.85),rgba(96,165,250,0.55),rgba(255,255,255,0))]" />
                    <p className="max-w-[22ch] text-[1.05rem] leading-9 text-slate-300">
                      atlas becomes the account, session, and trust layer for future self-hosted services.
                    </p>
                  </div>
                  <div className="flex items-center justify-between pt-8">
                    <p className="text-base font-medium lowercase text-sky-200">private app trust</p>
                    <div className="h-10 w-10 rounded-full bg-[linear-gradient(135deg,rgba(148,163,184,0.7),rgba(168,85,247,0.55))]" />
                  </div>
                </div>
              </div>
              <p className="text-sm font-medium lowercase text-sky-200">{productPillars[2].eyebrow}</p>
              <h3 className="mt-4 text-[1.9rem] leading-none font-semibold tracking-[-0.055em] text-white lowercase">
                {productPillars[2].title}
              </h3>
              <p className="mt-4 text-[1.02rem] leading-8 text-slate-300">{productPillars[2].body}</p>
            </motion.article>
          </motion.div>
        </motion.section>

        <motion.section
          className="mt-16 scroll-mt-28 md:mt-24 md:scroll-mt-32"
          id="resources"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={sectionReveal}
        >
          <div className="max-w-3xl">
            <p className="text-sm font-medium lowercase text-sky-200">resources</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-white lowercase md:text-4xl">
              built on clear contracts now, designed to expand carefully over time.
            </h2>
            <p className="mt-5 text-sm leading-7 text-slate-400">
              The current public core already defines the storage, auth, and session boundaries the product is growing
              around. The docs tell the rest of the story.
            </p>
          </div>

          <motion.div className="mt-8 grid gap-4 md:grid-cols-3" variants={staggerContainer}>
            {resourceBlocks.map((item) => (
              <motion.div key={item.title} variants={cardReveal}>
                <Link
                  to={item.href}
                  className="group flex h-full flex-col rounded-[1.6rem] border border-white/6 bg-white/2 p-6 transition duration-200 hover:border-white/10 hover:bg-white/3"
                >
                  <p className="text-sm font-medium lowercase text-sky-200">{item.label}</p>
                  <h3 className="mt-4 text-xl font-semibold tracking-[-0.04em] text-white lowercase">{item.title}</h3>
                  <p className="mt-3 text-sm leading-7 text-slate-400">{item.body}</p>
                  <p className="mt-6 text-sm text-slate-300 transition group-hover:text-white">open docs</p>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </motion.section>
      </section>
    </main>
  );
}
