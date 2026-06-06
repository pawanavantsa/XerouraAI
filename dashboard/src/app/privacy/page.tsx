import Link from "next/link";
import { BrandMark } from "@/components/BrandMark";

export default function PrivacyPolicyPage() {
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
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Privacy Policy</h1>
        <p className="text-sm text-slate-500 dark:text-slate-500 mb-10">Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}</p>

        <div className="prose-style space-y-8">
          <Section title="1. Information We Collect">
            <p>When you use Xeroura AI, we may collect the following types of information:</p>
            <ul>
              <li><strong>Account Information:</strong> Email address, team name, and password when you create an account.</li>
              <li><strong>Customer Conversations:</strong> Messages sent and received through connected channels (WhatsApp, Telegram, Email, Web Chat) are stored to provide the support service.</li>
              <li><strong>Channel Credentials:</strong> API tokens and configuration for WhatsApp, Telegram, and Gmail integrations that you provide.</li>
              <li><strong>Knowledge Base Data:</strong> Documents and FAQs you upload for AI-powered responses.</li>
              <li><strong>Usage Data:</strong> Basic analytics such as ticket counts, response times, and channel breakdown.</li>
            </ul>
          </Section>

          <Section title="2. How We Use Your Information">
            <ul>
              <li>To provide, maintain, and improve the AI customer support service.</li>
              <li>To classify, route, and respond to customer messages using AI (Claude by Anthropic).</li>
              <li>To display analytics and dashboard metrics to your team.</li>
              <li>To send customer responses through the appropriate channel.</li>
              <li>To store conversation history for agent review and escalation handling.</li>
            </ul>
          </Section>

          <Section title="3. Third-Party Services">
            <p>Xeroura AI integrates with the following third-party services:</p>
            <ul>
              <li><strong>Anthropic (Claude API):</strong> Customer messages are sent to Claude for classification and response generation. See <a href="https://www.anthropic.com/privacy" target="_blank" rel="noopener noreferrer">Anthropic&apos;s Privacy Policy</a>.</li>
              <li><strong>OpenAI:</strong> Used for text embeddings (knowledge base search). See <a href="https://openai.com/privacy" target="_blank" rel="noopener noreferrer">OpenAI&apos;s Privacy Policy</a>.</li>
              <li><strong>Meta (WhatsApp Business API):</strong> For WhatsApp messaging. See <a href="https://www.whatsapp.com/legal/privacy-policy" target="_blank" rel="noopener noreferrer">WhatsApp&apos;s Privacy Policy</a>.</li>
              <li><strong>Telegram Bot API:</strong> For Telegram messaging. See <a href="https://telegram.org/privacy" target="_blank" rel="noopener noreferrer">Telegram&apos;s Privacy Policy</a>.</li>
              <li><strong>Google (Gmail API):</strong> For email support. See <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">Google&apos;s Privacy Policy</a>.</li>
            </ul>
          </Section>

          <Section title="4. Data Storage & Security">
            <ul>
              <li>All data is stored in a PostgreSQL database within your self-hosted Docker deployment.</li>
              <li>Channel API tokens are stored in the database. We recommend encrypting these in production.</li>
              <li>Passwords are hashed using Django&apos;s default PBKDF2 algorithm.</li>
              <li>As a self-hosted solution, you maintain full control over your data.</li>
            </ul>
          </Section>

          <Section title="5. Data Retention">
            <p>Conversation data and knowledge base entries are retained indefinitely until you delete them. You can delete individual conversations, knowledge base entries, or your entire team account at any time.</p>
          </Section>

          <Section title="6. Your Rights">
            <ul>
              <li>Access, export, or delete your data at any time through the dashboard or database.</li>
              <li>Disconnect channel integrations to stop data collection from those channels.</li>
              <li>Delete your account and all associated data.</li>
            </ul>
          </Section>

          <Section title="7. Contact">
            <p>If you have questions about this privacy policy, please contact your deployment administrator or open an issue on the project repository.</p>
          </Section>
        </div>

        <div className="mt-12 pt-6 border-t border-slate-200/90 dark:border-slate-800 flex items-center justify-between">
          <Link href="/terms" className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline">Terms of Service &rarr;</Link>
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
