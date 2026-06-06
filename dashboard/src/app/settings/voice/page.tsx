"use client";

import Link from "next/link";

/**
 * Voice uses Twilio + server .env (no team DB form yet).
 * This page mirrors Settings → WhatsApp: step-by-step URLs and checklist.
 */
export default function VoiceSettingsPage() {
  const backendBase =
    typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}:8000`
      : "http://localhost:8000";

  const incomingUrl = `${backendBase}/api/webhooks/voice/incoming/`;

  return (
    <div className="p-8">
      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
        <Link href="/settings" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
          Settings
        </Link>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-gray-900 dark:text-white font-medium">Voice (phone calls)</span>
      </div>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Voice / phone calls</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Twilio Voice, speech-to-text on the call, AI replies, and tickets in the dashboard — same as chat.
        </p>
        <p className="text-sm text-teal-700 dark:text-teal-300 mt-2">
          Use the <Link href="/calls" className="font-semibold underline hover:no-underline">Calls</Link> page (sidebar, under Dashboard) to see live voice threads, get highlighted when a caller needs a human, and send audio to the caller.
        </p>
      </div>

      <div className="bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800/50 rounded-xl p-5 mb-6">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-100 dark:bg-teal-900/40 flex items-center justify-center shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-teal-800 dark:text-teal-300 mb-1">Configure in .env + Twilio Console</h3>
            <p className="text-xs text-teal-700 dark:text-teal-400/90 leading-relaxed">
              Credentials are read from the backend environment (Docker <code className="text-[11px]">.env</code>), not from this form.
              After editing <code className="text-[11px]">.env</code>, restart the backend container so variables reload.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 rounded-xl p-5 mb-6">
        <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-3">Twilio webhook (copy these URLs)</h3>
        <p className="text-xs text-amber-800/80 dark:text-amber-400/80 mb-3">
          In{" "}
          <span className="font-medium">Twilio Console → Phone Numbers → your number → Voice configuration</span>, set{" "}
          <strong>A call comes in</strong> to <strong>Webhook</strong>, HTTP <strong>POST</strong>, URL:
        </p>
        <code className="block px-3 py-2 bg-white dark:bg-slate-800 rounded-lg text-[11px] text-indigo-600 dark:text-indigo-400 font-mono break-all border border-amber-200/80 dark:border-amber-800/50">
          {incomingUrl}
        </code>
        <p className="text-xs text-amber-800/80 dark:text-amber-400/80 mt-3">
          For local development, run <code className="font-mono text-indigo-600 dark:text-indigo-400">ngrok http 8000</code> and use{" "}
          <code className="font-mono text-indigo-600 dark:text-indigo-400">https://&lt;your-ngrok&gt;/api/webhooks/voice/incoming/</code>{" "}
          instead. Set <code className="font-mono">PUBLIC_BASE_URL</code> in <code className="font-mono">.env</code> to that same{" "}
          <strong>https</strong> origin so Twilio can fetch AI audio (<code className="font-mono">&lt;Play&gt;</code>) and redirects.
        </p>
        <p className="text-xs text-amber-800/80 dark:text-amber-400/80 mt-2">
          Add your ngrok host to <code className="font-mono">ALLOWED_HOSTS</code> in <code className="font-mono">.env</code> (e.g.{" "}
          <code className="font-mono">.ngrok-free.app</code>) or Django will return 400/disallowed host.
        </p>
        <Link
          href="/docs"
          className="inline-flex items-center gap-1 mt-3 text-xs font-medium text-amber-700 dark:text-amber-400 hover:text-amber-900 dark:hover:text-amber-300"
        >
          Full step-by-step in Documentation
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700 shadow-sm p-6 space-y-5">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Checklist</h2>
        <ol className="list-decimal list-inside space-y-3 text-sm text-gray-600 dark:text-gray-400">
          <li>
            <a
              href="https://www.twilio.com/try-twilio"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Twilio account
            </a>{" "}
            — copy <strong>Account SID</strong> and <strong>Auth Token</strong> from the Console dashboard.
          </li>
          <li>
            Buy or use a Twilio number with <strong>Voice</strong> capability; paste the webhook URL above for <strong>incoming voice calls</strong>.
          </li>
          <li>
            In project <code className="text-xs font-mono bg-gray-100 dark:bg-slate-700 px-1 rounded">.env</code> set:
            <ul className="list-disc list-inside mt-2 text-xs font-mono text-gray-500 dark:text-gray-400 space-y-1">
              <li>TWILIO_ACCOUNT_SID=AC...</li>
              <li>TWILIO_AUTH_TOKEN=...</li>
              <li>PUBLIC_BASE_URL=https://your-ngrok-host (required for TTS audio URLs when using ngrok)</li>
            </ul>
          </li>
          <li>
            Optional — natural AI voice: <code className="text-xs font-mono">ELEVENLABS_API_KEY</code>,{" "}
            <code className="text-xs font-mono">ELEVENLABS_VOICE_ID</code> (otherwise Amazon Polly speaks the reply).
          </li>
          <li>
            Optional — on &quot;I need a human&quot;, forward the call to your cell:{" "}
            <code className="text-xs font-mono">VOICE_ESCALATION_FORWARD_NUMBER=+15551234567</code> (E.164).
          </li>
          <li>
            Restart backend: <code className="text-xs font-mono bg-gray-100 dark:bg-slate-700 px-1 rounded">docker compose up -d --build</code> or restart the{" "}
            <code className="text-xs font-mono">backend</code> service.
          </li>
          <li>
            Call your Twilio number — you should hear the greeting, speak, get an AI answer, and see a <strong>voice</strong> ticket under Tickets.
          </li>
          <li>
            While the caller is still connected, an agent can use <strong>Send</strong> on that ticket; the text is played on the call via Twilio (if the call is still active).
          </li>
        </ol>
      </div>

      <p className="mt-6 text-xs text-gray-500 dark:text-gray-400">
        Architecture, scaling, and security notes: see the repo file{" "}
        <code className="font-mono text-gray-600 dark:text-gray-300">docs/VOICE_AND_CALLS.md</code>.
      </p>
    </div>
  );
}
