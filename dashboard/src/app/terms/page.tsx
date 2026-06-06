import Link from "next/link";
import { BrandMark } from "@/components/BrandMark";

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-[#f8fafc] dark:bg-slate-950">
      {/* Nav */}
      <nav className="sticky top-0 z-40 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <BrandMark size="sm" />
          <Link href="/" className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 transition-colors">
            &larr; Back to home
          </Link>
        </div>
      </nav>

      <article className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Terms of Service</h1>
        <p className="text-sm text-slate-500 dark:text-slate-500 mb-10">Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</p>

        <div className="prose-style space-y-8">
          <Section title="1. Acceptance of Terms">
            <p>By accessing or using Xeroura AI (&quot;the Service&quot;), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.</p>
          </Section>

          <Section title="2. Description of Service">
            <p>Xeroura AI is a self-hosted, open-source AI customer support platform that:</p>
            <ul>
              <li>Receives customer messages from WhatsApp, Telegram, Email, and Web Chat.</li>
              <li>Uses AI (Claude by Anthropic) to classify, route, and respond to support tickets.</li>
              <li>Provides a dashboard for human agents to manage escalated tickets.</li>
              <li>Stores conversations and knowledge base data in a self-hosted PostgreSQL database.</li>
            </ul>
          </Section>

          <Section title="3. User Accounts">
            <ul>
              <li>You must provide accurate information when creating an account.</li>
              <li>You are responsible for maintaining the security of your account credentials.</li>
              <li>You are responsible for all activity under your account.</li>
              <li>You must notify us immediately of any unauthorized access.</li>
            </ul>
          </Section>

          <Section title="4. Acceptable Use">
            <p>You agree NOT to:</p>
            <ul>
              <li>Use the Service for any illegal or unauthorized purpose.</li>
              <li>Send spam, unsolicited messages, or bulk marketing through the Service.</li>
              <li>Attempt to reverse-engineer, decompile, or hack the Service beyond its intended open-source use.</li>
              <li>Upload malicious content to the knowledge base.</li>
              <li>Violate the terms of any connected third-party service (WhatsApp, Telegram, Gmail).</li>
            </ul>
          </Section>

          <Section title="5. Third-Party Services">
            <p>The Service integrates with third-party APIs. You are responsible for:</p>
            <ul>
              <li>Complying with Meta&apos;s (WhatsApp) terms and policies.</li>
              <li>Complying with Telegram&apos;s Bot API terms.</li>
              <li>Complying with Google&apos;s Gmail API terms and usage policies.</li>
              <li>Complying with Anthropic&apos;s acceptable use policy for the Claude API.</li>
              <li>Complying with OpenAI&apos;s usage policies for embeddings.</li>
            </ul>
          </Section>

          <Section title="6. Data & Privacy">
            <ul>
              <li>As a self-hosted solution, you control all data storage and processing.</li>
              <li>You are responsible for complying with applicable data protection laws (GDPR, CCPA, etc.) in your jurisdiction.</li>
              <li>Customer messages are processed through third-party AI APIs — you must inform your customers accordingly.</li>
              <li>See our <Link href="/privacy" className="text-indigo-600 dark:text-indigo-400 underline">Privacy Policy</Link> for more details.</li>
            </ul>
          </Section>

          <Section title="7. Intellectual Property">
            <ul>
              <li>Xeroura AI is open-source software. The source code is available under its respective license.</li>
              <li>You retain ownership of all data you input into the Service (conversations, knowledge base, etc.).</li>
              <li>The &quot;Xeroura AI&quot; name and branding are used in connection with this software.</li>
            </ul>
          </Section>

          <Section title="8. Disclaimer of Warranties">
            <p>The Service is provided &quot;AS IS&quot; and &quot;AS AVAILABLE&quot; without warranties of any kind. We do not guarantee that:</p>
            <ul>
              <li>AI-generated responses will be accurate, complete, or appropriate.</li>
              <li>The Service will be uninterrupted or error-free.</li>
              <li>The AI will not occasionally produce incorrect or misleading responses despite guardrails.</li>
            </ul>
            <p><strong>Human oversight is required.</strong> The Service is designed as a hybrid system where AI handles routine queries and humans handle complex ones.</p>
          </Section>

          <Section title="9. Limitation of Liability">
            <p>To the maximum extent permitted by law, Xeroura AI and its contributors shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the Service.</p>
          </Section>

          <Section title="10. Changes to Terms">
            <p>We reserve the right to modify these terms at any time. Continued use of the Service after changes constitutes acceptance of the updated terms.</p>
          </Section>

          <Section title="11. Contact">
            <p>For questions about these terms, please reach out through the GitHub repository or your deployment administrator.</p>
          </Section>
        </div>

        <div className="mt-12 pt-6 border-t border-slate-200/90 dark:border-slate-800 flex items-center justify-between">
          <Link href="/privacy" className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline">&larr; Privacy Policy</Link>
          <Link href="/" className="text-sm text-slate-500 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors">Back to home</Link>
        </div>
      </article>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">{title}</h2>
      <div className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed space-y-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-2 [&_a]:text-indigo-600 dark:[&_a]:text-indigo-400 [&_a]:underline">
        {children}
      </div>
    </section>
  );
}
