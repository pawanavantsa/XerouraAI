"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { useTheme } from "@/lib/theme";
import { BrandMark } from "@/components/BrandMark";
import { easeFluid, navTransition, scrollViewport, springSoft, staggerChildren } from "@/lib/motionPresets";
import SupportFlowDiagram from "./SupportFlowDiagram";

/* ── Fake chat demo messages ── */
const DEMO_MESSAGES = [
  { role: "customer", text: "Hi, I was charged twice for my subscription last month. Can you help?" },
  { role: "ai", text: "I understand how frustrating that must be. Let me look into your billing records right away. Could you share your account email so I can pull up the details?" },
  { role: "customer", text: "Sure, it's pawan@example.com" },
  { role: "ai", text: "Thanks Pawan! I found the duplicate charge of $29.99 on March 3rd. I've initiated a refund — you should see it in 3-5 business days. Is there anything else I can help with?" },
];

/** Fade/slide in when the block scrolls into view; replays when scrolling back (unless reduced motion). */
const scrollReveal = (reduced: boolean | null, i: number, y = 22) => ({
  initial: reduced ? false : { opacity: 0, y },
  whileInView: { opacity: 1, y: 0 },
  viewport: scrollViewport(reduced),
  transition: reduced
    ? { duration: 0 }
    : { duration: 0.55, ease: easeFluid, delay: staggerChildren(reduced) * i },
});

export function LandingPage() {
  const { theme, toggleTheme } = useTheme();
  const reducedMotion = useReducedMotion();
  const { scrollY } = useScroll();
  const [demoChatVisible, setDemoChatVisible] = useState(3); // show first N messages

  const parallax = !reducedMotion;
  const blobRightY = useTransform(scrollY, [0, 520], [0, parallax ? 105 : 0]);
  const blobLeftY = useTransform(scrollY, [0, 520], [0, parallax ? -82 : 0]);
  const gridShiftY = useTransform(scrollY, [0, 420], [0, parallax ? 36 : 0]);
  const navShadow = useTransform(
    scrollY,
    [0, 32, 120],
    [
      "0 0 0 0 rgba(15,23,42,0)",
      "0 12px 40px -16px rgba(15, 23, 42, 0.07)",
      "0 16px 48px -14px rgba(15, 23, 42, 0.09)",
    ],
  );

  // Animate showing messages
  const showNextMessage = () => {
    if (demoChatVisible < DEMO_MESSAGES.length) {
      setDemoChatVisible((p) => p + 1);
    } else {
      setDemoChatVisible(1);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] dark:bg-slate-950 text-gray-900 dark:text-white antialiased selection:bg-indigo-500/20 selection:text-indigo-900 dark:selection:text-white">
      {/* ═══ Navigation ═══ */}
      <motion.nav
        initial={reducedMotion ? false : { opacity: 0, y: -14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={navTransition(reducedMotion)}
        style={{ boxShadow: navShadow }}
        className="sticky top-0 z-50 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/75 dark:bg-slate-950/75 backdrop-blur-xl supports-[backdrop-filter]:bg-white/60"
      >
        <div className="max-w-7xl mx-auto px-6 h-[4.25rem] flex items-center justify-between">
          <BrandMark size="md" />

          <div className="hidden md:flex items-center gap-1">
            {[
              { href: "#features", label: "Features" },
              { href: "#how-it-works", label: "How It Works" },
              { href: "#tech-stack", label: "Tech Stack" },
            ].map((l) => (
              <motion.a
                key={l.href}
                href={l.href}
                whileHover={reducedMotion ? undefined : { y: -1 }}
                whileTap={reducedMotion ? undefined : { scale: 0.98 }}
                className="text-sm text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-lg transition-colors"
              >
                {l.label}
              </motion.a>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <motion.button
              type="button"
              onClick={toggleTheme}
              title={theme === "dark" ? "Light mode" : "Dark mode"}
              whileHover={reducedMotion ? undefined : { scale: 1.05 }}
              whileTap={reducedMotion ? undefined : { scale: 0.95 }}
              className="p-2.5 rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              {theme === "dark" ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
              )}
            </motion.button>
            <Link href="/login" className="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white px-3 py-2 transition-colors">Login</Link>
            <motion.div whileHover={reducedMotion ? undefined : { y: -1 }} whileTap={reducedMotion ? undefined : { scale: 0.98 }}>
              <Link
                href="/signup"
                className="inline-block text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 px-4 py-2.5 rounded-xl transition-all shadow-md shadow-indigo-500/20 ring-1 ring-white/10"
              >
                Get Started
              </Link>
            </motion.div>
          </div>
        </div>
      </motion.nav>

      {/* ═══ Hero — Split: Left text, Right chat demo ═══ */}
      <section className="relative overflow-hidden pt-14 pb-24 px-6">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <motion.div
            style={{ y: blobRightY }}
            className="absolute -top-24 -right-24 h-[28rem] w-[28rem] rounded-full bg-gradient-to-br from-indigo-400/20 via-violet-400/15 to-transparent blur-3xl dark:from-indigo-500/15 dark:via-violet-500/10"
            animate={reducedMotion ? undefined : { scale: [1, 1.07, 1], opacity: [0.45, 0.62, 0.45] }}
            transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            style={{ y: blobLeftY }}
            className="absolute top-40 -left-32 h-[22rem] w-[22rem] rounded-full bg-gradient-to-tr from-teal-400/15 to-transparent blur-3xl dark:from-teal-500/10"
            animate={reducedMotion ? undefined : { scale: [1, 1.05, 1], opacity: [0.35, 0.5, 0.35] }}
            transition={{ duration: 18, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          />
          <motion.div
            style={{ y: gridShiftY }}
            className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,rgba(51,65,85,0.35)_1px,transparent_1px),linear-gradient(to_bottom,rgba(51,65,85,0.35)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:linear-gradient(to_bottom,black,transparent)] opacity-40 dark:opacity-30"
          />
        </div>

        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-14 lg:gap-16 items-center">
          {/* Left: Copy */}
          <div className="relative z-[1]">
            <motion.h1
              {...scrollReveal(reducedMotion, 0)}
              className="text-[2.35rem] sm:text-5xl lg:text-[3.15rem] font-bold tracking-tight text-slate-900 dark:text-white leading-[1.1] mb-6"
            >
              AI Customer Support
              <span className="block mt-2 bg-gradient-to-r from-indigo-600 via-violet-600 to-fuchsia-500 bg-clip-text text-transparent">
                That Actually Works
              </span>
            </motion.h1>

            <motion.p
              {...scrollReveal(reducedMotion, 1)}
              className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 mb-8 leading-relaxed max-w-xl"
            >
              Handle <span className="font-semibold text-slate-900 dark:text-white">90% of support tickets</span>{" "}
              automatically. WhatsApp, Telegram, Email, Web Chat, and Phone (Twilio Voice) — all feeding into one AI
              brain.
            </motion.p>

            {/* Key stats */}
            <motion.div {...scrollReveal(reducedMotion, 2)} className="flex flex-wrap gap-8 mb-10">
              {[
                { value: "90%", label: "Auto-resolved" },
                { value: "<2s", label: "Response time" },
                { value: "5", label: "Channels" },
              ].map((s) => (
                <div key={s.label}>
                  <p className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent tabular-nums">
                    {s.value}
                  </p>
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mt-1">
                    {s.label}
                  </p>
                </div>
              ))}
            </motion.div>

            <motion.div {...scrollReveal(reducedMotion, 3)} className="flex items-center gap-4 mb-10">
              <motion.a
                href="#how-it-works"
                whileHover={reducedMotion ? undefined : { scale: 1.02, y: -2 }}
                whileTap={reducedMotion ? undefined : { scale: 0.98 }}
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-500/25 ring-1 ring-white/10 transition-all"
              >
                See How It Works
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </motion.a>
            </motion.div>

            {/* Channel badges */}
            <motion.div {...scrollReveal(reducedMotion, 4)} className="flex flex-wrap items-center gap-2">
              {[
                { name: "WhatsApp", color: "bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 border-emerald-500/20" },
                { name: "Telegram", color: "bg-sky-500/10 text-sky-800 dark:text-sky-300 border-sky-500/20" },
                { name: "Email", color: "bg-rose-500/10 text-rose-800 dark:text-rose-300 border-rose-500/20" },
                { name: "Web Chat", color: "bg-violet-500/10 text-violet-800 dark:text-violet-300 border-violet-500/20" },
                { name: "Phone", color: "bg-teal-500/10 text-teal-800 dark:text-teal-300 border-teal-500/20" },
              ].map((ch, bi) => (
                <motion.span
                  key={ch.name}
                  initial={reducedMotion ? false : { opacity: 0, scale: 0.92 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={scrollViewport(reducedMotion)}
                  transition={
                    reducedMotion
                      ? { duration: 0 }
                      : { delay: 0.35 + bi * 0.05, duration: 0.4, ease: easeFluid }
                  }
                  whileHover={reducedMotion ? undefined : { y: -2, scale: 1.03 }}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium border backdrop-blur-sm ${ch.color}`}
                >
                  {ch.name}
                </motion.span>
              ))}
            </motion.div>
          </div>

          {/* Right: Chat demo widget */}
          <motion.div
            className="relative"
            initial={reducedMotion ? false : { opacity: 0, y: 32, scale: 0.96 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={scrollViewport(reducedMotion)}
            transition={reducedMotion ? { duration: 0 } : { ...springSoft, delay: 0.12 }}
          >
            <div className="absolute -inset-1 rounded-[1.35rem] bg-gradient-to-br from-indigo-500/20 via-violet-500/10 to-teal-500/20 blur-sm dark:opacity-80" aria-hidden />
            <div className="relative bg-white dark:bg-slate-900/90 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 shadow-2xl shadow-slate-900/10 dark:shadow-black/40 overflow-hidden max-w-md mx-auto ring-1 ring-slate-900/5 dark:ring-white/5">
              {/* Chat header */}
              <div className="px-5 py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Xeroura AI</p>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <p className="text-[11px] text-indigo-200">Online &middot; Replies in seconds</p>
                  </div>
                </div>
              </div>

              {/* Chat messages */}
              <div className="px-4 py-5 space-y-3 min-h-[320px] bg-slate-50/90 dark:bg-slate-950/50">
                {DEMO_MESSAGES.slice(0, demoChatVisible).map((msg, i) => (
                  <motion.div
                    key={`${msg.role}-${i}-${msg.text.slice(0, 24)}`}
                    layout={!reducedMotion}
                    initial={reducedMotion ? false : { opacity: 0, y: 12, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.38, ease: easeFluid }}
                    className={`flex ${msg.role === "ai" ? "justify-start" : "justify-end"}`}
                  >
                    <div className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-[13px] leading-relaxed ${
                      msg.role === "ai"
                        ? "bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 text-gray-700 dark:text-gray-300 rounded-bl-md"
                        : "bg-indigo-600 text-white rounded-br-md"
                    }`}>
                      {msg.role === "ai" && (
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">AI Agent</span>
                          <span className="text-[10px] text-gray-400">just now</span>
                        </div>
                      )}
                      {msg.text}
                    </div>
                  </motion.div>
                ))}

                {demoChatVisible < DEMO_MESSAGES.length && (
                  <div className="flex justify-start">
                    <div className="bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 rounded-2xl rounded-bl-md px-4 py-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-gray-300 dark:bg-slate-600 animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-2 h-2 rounded-full bg-gray-300 dark:bg-slate-600 animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-2 h-2 rounded-full bg-gray-300 dark:bg-slate-600 animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat input */}
              <div className="px-4 py-3 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
                <button
                  onClick={showNextMessage}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-50 dark:bg-slate-700 rounded-xl text-sm text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors"
                >
                  <span>{demoChatVisible >= DEMO_MESSAGES.length ? "Restart demo..." : "Click to see AI respond..."}</span>
                  <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                </button>
              </div>
            </div>

            {/* Floating badge */}
            <motion.div
              initial={reducedMotion ? false : { opacity: 0, x: -12, y: 8 }}
              whileInView={{ opacity: 1, x: 0, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={reducedMotion ? { duration: 0 } : { delay: 0.48, duration: 0.5, ease: easeFluid }}
              className="absolute -bottom-4 -left-4 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-3.5 py-2 rounded-xl text-xs font-semibold shadow-lg shadow-emerald-500/25 ring-1 ring-white/20 hidden lg:block"
            >
              Classified as: Billing
            </motion.div>
            <motion.div
              initial={reducedMotion ? false : { opacity: 0, x: 12, y: -8 }}
              whileInView={{ opacity: 1, x: 0, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={reducedMotion ? { duration: 0 } : { delay: 0.55, duration: 0.5, ease: easeFluid }}
              className="absolute -top-3 -right-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white px-3.5 py-2 rounded-xl text-xs font-semibold shadow-lg shadow-amber-500/25 ring-1 ring-white/20 hidden lg:block"
            >
              Confidence: 94%
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══ "The Problem" section — why this exists ═══ */}
      <section className="py-20 px-6 border-y border-slate-200/80 dark:border-slate-800/80 bg-white/60 dark:bg-slate-900/40 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto text-center">
          <motion.h2
            initial={reducedMotion ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={scrollViewport(reducedMotion)}
            transition={{ duration: 0.55, ease: easeFluid }}
            className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 dark:text-white mb-4"
          >
            The 90/10 Approach to Support
          </motion.h2>
          <motion.p
            initial={reducedMotion ? false : { opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={scrollViewport(reducedMotion)}
            transition={{ duration: 0.55, ease: easeFluid, delay: reducedMotion ? 0 : 0.06 }}
            className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-12 text-lg leading-relaxed"
          >
            90% of support tickets are repetitive — billing questions, password resets, shipping status.
            AI handles those instantly. Humans focus on the complex 10% that actually needs them.
          </motion.p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              { icon: "🤖", title: "AI Handles 90%", desc: "Billing, shipping, FAQs, account questions — answered in seconds from your knowledge base", ring: "from-indigo-500/20 to-violet-500/10", bg: "bg-white/80 dark:bg-slate-900/60" },
              { icon: "👤", title: "Humans Handle 10%", desc: "Complex issues, angry customers, edge cases — with full AI-generated context & suggested replies", ring: "from-amber-500/20 to-orange-500/10", bg: "bg-white/80 dark:bg-slate-900/60" },
              { icon: "🛡️", title: "3 Safety Layers", desc: "Anti-hallucination guardrails ensure AI never makes up policies, prices, or guarantees", ring: "from-rose-500/20 to-pink-500/10", bg: "bg-white/80 dark:bg-slate-900/60" },
            ].map((item, ci) => (
              <motion.div
                key={item.title}
                initial={reducedMotion ? false : { opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={scrollViewport(reducedMotion)}
                transition={{ duration: 0.5, ease: easeFluid, delay: reducedMotion ? 0 : 0.08 + ci * 0.1 }}
                whileHover={reducedMotion ? undefined : { y: -4, transition: { duration: 0.25, ease: easeFluid } }}
                className={`relative rounded-2xl p-6 text-left border border-slate-200/90 dark:border-slate-700/80 shadow-lg shadow-slate-900/5 dark:shadow-black/20 ${item.bg}`}
              >
                <div
                  className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${item.ring} opacity-60 -z-10`}
                  aria-hidden
                />
                <span className="text-3xl mb-3 block">{item.icon}</span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">{item.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ Features Grid ═══ */}
      <section id="features" className="py-24 px-6 relative">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-slate-200 dark:via-slate-700 to-transparent" aria-hidden />
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <motion.span
              initial={reducedMotion ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={{ duration: 0.5, ease: easeFluid }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-500/10 text-violet-700 dark:text-violet-300 text-xs font-semibold tracking-wide uppercase border border-violet-500/15 mb-5"
            >
              Key Features
            </motion.span>
            <motion.h2
              initial={reducedMotion ? false : { opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={{ duration: 0.55, ease: easeFluid, delay: reducedMotion ? 0 : 0.04 }}
              className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-white mb-4"
            >
              Everything You Need
            </motion.h2>
            <motion.p
              initial={reducedMotion ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={{ duration: 0.5, ease: easeFluid, delay: reducedMotion ? 0 : 0.08 }}
              className="text-slate-600 dark:text-slate-400 max-w-xl mx-auto text-lg"
            >
              Built with modern tools — no bloat, no vendor lock-in, fully open source.
            </motion.p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, fi) => (
              <motion.div
                key={feature.title}
                initial={reducedMotion ? false : { opacity: 0, y: 22 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={scrollViewport(reducedMotion)}
                transition={{ duration: 0.5, ease: easeFluid, delay: reducedMotion ? 0 : fi * 0.06 }}
                whileHover={reducedMotion ? undefined : { y: -3 }}
                className="group relative rounded-2xl p-6 border border-slate-200/90 dark:border-slate-700/80 bg-white/90 dark:bg-slate-900/50 shadow-sm hover:shadow-xl hover:shadow-indigo-500/5 dark:hover:shadow-black/30 hover:border-indigo-300/50 dark:hover:border-indigo-500/30 transition-all duration-300"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${feature.iconBg} ring-1 ring-black/5 dark:ring-white/10 group-hover:scale-105 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ How It Works — Animated Flow Diagram ═══ */}
      <div className="relative bg-slate-100/80 dark:bg-slate-900/50 border-y border-slate-200/80 dark:border-slate-800/80">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent" aria-hidden />
        <motion.div
          initial={reducedMotion ? false : { opacity: 0, y: 28 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={scrollViewport(reducedMotion)}
          transition={{ duration: 0.65, ease: easeFluid }}
        >
          <SupportFlowDiagram />
        </motion.div>
      </div>

      {/* ═══ Tech Stack ═══ */}
      <section id="tech-stack" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <motion.span
              initial={reducedMotion ? false : { opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={{ duration: 0.45, ease: easeFluid }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 text-cyan-800 dark:text-cyan-300 text-xs font-semibold tracking-wide uppercase border border-cyan-500/15 mb-5"
            >
              Under The Hood
            </motion.span>
            <motion.h2
              initial={reducedMotion ? false : { opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={scrollViewport(reducedMotion)}
              transition={{ duration: 0.5, ease: easeFluid, delay: reducedMotion ? 0 : 0.05 }}
              className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-white mb-3"
            >
              Built With
            </motion.h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {TECH_STACK.map((tech, ti) => (
              <motion.div
                key={tech.name}
                initial={reducedMotion ? false : { opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={scrollViewport(reducedMotion)}
                transition={{ duration: 0.45, ease: easeFluid, delay: reducedMotion ? 0 : ti * 0.05 }}
                whileHover={reducedMotion ? undefined : { y: -3 }}
                className="rounded-2xl border border-slate-200/90 dark:border-slate-700/80 bg-white/90 dark:bg-slate-900/40 p-5 text-center hover:shadow-lg hover:shadow-slate-900/5 dark:hover:shadow-black/30 transition-all duration-300"
              >
                <span className="text-2xl mb-2 block">{tech.icon}</span>
                <p className="text-sm font-semibold text-slate-900 dark:text-white">{tech.name}</p>
                <p className="text-[11px] text-slate-500 dark:text-slate-500 mt-1">{tech.role}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ Footer ═══ */}
      <motion.footer
        initial={reducedMotion ? false : { opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={scrollViewport(reducedMotion)}
        transition={{ duration: 0.6, ease: easeFluid }}
        className="border-t border-slate-200/90 dark:border-slate-800 bg-slate-50/90 dark:bg-slate-950 pt-14 pb-10 px-6"
      >
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-12">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-500/20">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                </div>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">Xeroura AI</span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed max-w-[16rem]">
                AI-powered multi-channel customer support. Handle 90% of tickets automatically.
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">Product</h4>
              <ul className="space-y-2">
                <li><a href="#features" className="text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">How It Works</a></li>
                <li><Link href="/docs" className="text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Documentation</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">Channels</h4>
              <ul className="space-y-2">
                <li><span className="text-sm text-slate-500 dark:text-slate-400">WhatsApp Business</span></li>
                <li><span className="text-sm text-slate-500 dark:text-slate-400">Telegram</span></li>
                <li><span className="text-sm text-slate-500 dark:text-slate-400">Gmail / Email</span></li>
                <li><span className="text-sm text-slate-500 dark:text-slate-400">Web Chat Widget</span></li>
                <li><span className="text-sm text-slate-500 dark:text-slate-400">Phone (Twilio Voice)</span></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">Legal</h4>
              <ul className="space-y-2">
                <li><Link href="/privacy" className="text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Privacy Policy</Link></li>
                <li><Link href="/terms" className="text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="pt-6 border-t border-slate-200/90 dark:border-slate-800 flex flex-col md:flex-row items-center justify-between gap-3">
            <p className="text-xs text-slate-500 dark:text-slate-500">&copy; {new Date().getFullYear()} Xeroura AI</p>
            <div className="flex items-center gap-4">
              <Link href="/privacy" className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Privacy</Link>
              <Link href="/terms" className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Terms</Link>
            </div>
          </div>
        </div>
      </motion.footer>
    </div>
  );
}

/* ── Feature data ── */
const FEATURES = [
  { title: "Multi-Channel Support", description: "WhatsApp, Telegram, Email, Web Chat, and Phone (Twilio Voice) — all conversations flow into one unified dashboard.", iconBg: "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400", icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" /></svg> },
  { title: "AI Classification", description: "Claude Haiku auto-routes tickets — billing, technical, account, or complaint — with confidence scoring.", iconBg: "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400", icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg> },
  { title: "RAG Responses", description: "Claude Sonnet generates answers using your knowledge base via pgvector semantic search. No hallucinations.", iconBg: "bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400", icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg> },
  { title: "Smart Escalation", description: "Auto-escalates when confidence < 70%, customer is frustrated, or asks for a human. Full context handoff.", iconBg: "bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400", icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg> },
  { title: "Agent Dashboard", description: "Real-time ticket queue, conversation view, AI sidebar with suggestions, analytics — all in one place.", iconBg: "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400", icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> },
  { title: "Anti-Hallucination", description: "3-layer guardrails: system prompt constraints, empty RAG fallback, post-generation policy/price check.", iconBg: "bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400", icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg> },
];

/* ── Tech stack data ── */
const TECH_STACK = [
  { icon: "🐍", name: "Django", role: "Backend + REST API" },
  { icon: "⚛️", name: "Next.js", role: "Agent Dashboard" },
  { icon: "🧠", name: "Claude AI", role: "Haiku + Sonnet" },
  { icon: "🐘", name: "PostgreSQL", role: "Database + pgvector" },
  { icon: "🔴", name: "Redis", role: "WebSocket Channels" },
  { icon: "🐳", name: "Docker", role: "One-command deploy" },
  { icon: "📡", name: "ngrok", role: "Webhook tunneling" },
  { icon: "🔑", name: "JWT Auth", role: "Team authentication" },
];
