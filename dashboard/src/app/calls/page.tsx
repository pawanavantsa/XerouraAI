"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import ConversationThread from "@/components/ConversationThread";
import { API_URL, bearerHeaders } from "@/lib/api";

interface QueueRow {
  id: string;
  sender_id: string;
  sender_name: string;
  status: string;
  human_only: boolean;
  last_voice_call_sid: string;
  needs_human: boolean;
  has_live_call_hint: boolean;
  escalation_id?: string | null;
  last_customer_preview: string;
  updated_at: string;
}

interface Message {
  id: string;
  role: "customer" | "ai" | "agent";
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

interface CallDetail {
  id: string;
  channel: string;
  status: string;
  sender_name: string;
  sender_id?: string;
  human_only?: boolean;
  last_voice_call_sid?: string;
  escalation_id?: string;
  messages: Message[];
}

export default function CallsPage() {
  const [queue, setQueue] = useState<QueueRow[]>([]);
  const [needsCount, setNeedsCount] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CallDetail | null>(null);
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const fetchQueue = useCallback(() => {
    fetch(`${API_URL}/api/voice/calls/`, { headers: bearerHeaders() })
      .then((r) => r.json())
      .then((data) => {
        setQueue(Array.isArray(data.calls) ? data.calls : []);
        setNeedsCount(typeof data.needs_attention_count === "number" ? data.needs_attention_count : 0);
      })
      .catch(() => {
        setQueue([]);
        setNeedsCount(0);
      })
      .finally(() => setLoadingQueue(false));
  }, []);

  const fetchDetail = useCallback((id: string) => {
    setLoadingDetail(true);
    fetch(`${API_URL}/api/conversations/${id}/`, { headers: bearerHeaders() })
      .then((r) => r.json())
      .then((data) => setDetail(data))
      .catch(() => setDetail(null))
      .finally(() => setLoadingDetail(false));
  }, []);

  useEffect(() => {
    fetchQueue();
    const q = setInterval(fetchQueue, 6000);
    return () => clearInterval(q);
  }, [fetchQueue]);

  useEffect(() => {
    if (selectedId !== null || queue.length === 0) return;
    const urgent = queue.find((r) => r.needs_human);
    setSelectedId(urgent?.id ?? queue[0].id);
  }, [queue, selectedId]);

  useEffect(() => {
    if (!selectedId || queue.length === 0) return;
    if (!queue.some((r) => r.id === selectedId)) {
      setSelectedId(null);
    }
  }, [queue, selectedId]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    fetchDetail(selectedId);
    const d = setInterval(() => fetchDetail(selectedId), 5000);
    return () => clearInterval(d);
  }, [selectedId, fetchDetail]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2800);
  };

  const handleSendToCaller = async () => {
    if (!replyText.trim() || !detail) return;
    setSending(true);
    try {
      const res = await fetch(`${API_URL}/api/conversations/${detail.id}/reply/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...bearerHeaders() },
        body: JSON.stringify({ message: replyText.trim(), agent_name: "Voice agent" }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setReplyText("");
        showToast(data.sent ? "Played on the caller's line" : "Saved — call may have ended (Twilio inactive)");
        fetchDetail(detail.id);
        fetchQueue();
      } else {
        showToast("Could not send");
      }
    } catch {
      showToast("Could not send");
    } finally {
      setSending(false);
    }
  };

  const handleToggleHumanOnly = async () => {
    if (!detail) return;
    try {
      const res = await fetch(`${API_URL}/api/conversations/${detail.id}/toggle-human-only/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...bearerHeaders() },
        body: JSON.stringify({ human_only: !detail.human_only }),
      });
      if (res.ok) {
        fetchDetail(detail.id);
        fetchQueue();
        showToast(detail.human_only ? "AI can respond again on new turns" : "Human only — AI muted for new speech");
      }
    } catch {
      /* silent */
    }
  };

  const handleResolve = async () => {
    if (!detail?.escalation_id || !replyText.trim()) return;
    setResolving(true);
    try {
      const res = await fetch(`${API_URL}/api/escalations/${detail.escalation_id}/resolve/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...bearerHeaders() },
        body: JSON.stringify({
          agent_name: "Voice agent",
          response: replyText.trim(),
        }),
      });
      if (res.ok) {
        setReplyText("");
        showToast("Resolved and message sent to caller if possible");
        fetchDetail(detail.id);
        fetchQueue();
      }
    } catch {
      /* silent */
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-0px)] min-h-[480px]">
      {toast && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm shadow-lg">
          {toast}
        </div>
      )}

      <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Calls</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              Live phone conversations — AI answers first; take over when the caller needs a human.
            </p>
          </div>
          {needsCount > 0 ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-100 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200 text-xs font-semibold animate-pulse">
              <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
              {needsCount} need{needsCount === 1 ? "s" : ""} a human
            </div>
          ) : (
            <span className="text-xs text-gray-400 dark:text-gray-500">No human requests waiting</span>
          )}
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Queue */}
        <aside className="w-full max-w-sm border-r border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col shrink-0">
          <div className="px-3 py-2 border-b border-gray-100 dark:border-slate-700 text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            Active calls
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loadingQueue && queue.length === 0 ? (
              <p className="text-sm text-gray-400 p-3">Loading…</p>
            ) : queue.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 p-3">
                No active voice threads. When someone calls your Twilio number, they appear here.
              </p>
            ) : (
              queue.map((row) => (
                <button
                  key={row.id}
                  type="button"
                  onClick={() => setSelectedId(row.id)}
                  className={`w-full text-left rounded-xl px-3 py-2.5 transition-colors border ${
                    selectedId === row.id
                      ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-800"
                      : row.needs_human
                        ? "bg-amber-50/80 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800/60 hover:bg-amber-50 dark:hover:bg-amber-950/40"
                        : "border-transparent hover:bg-gray-50 dark:hover:bg-slate-700/50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                      {row.sender_name || row.sender_id || "Caller"}
                    </span>
                    {row.needs_human ? (
                      <span className="shrink-0 text-[10px] font-bold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                        Human
                      </span>
                    ) : null}
                  </div>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate mt-0.5">
                    {row.last_customer_preview || "—"}
                  </p>
                  <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-400">
                    <span className="capitalize">{row.status}</span>
                    {row.has_live_call_hint ? (
                      <span className="text-teal-600 dark:text-teal-400">Possible live call</span>
                    ) : null}
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* Detail */}
        <section className="flex-1 flex flex-col min-w-0 bg-gray-50/50 dark:bg-slate-900/50">
          {!selectedId ? (
            <div className="flex-1 flex items-center justify-center p-8 text-center text-gray-500 dark:text-gray-400 text-sm">
              Select a call to see the transcript and speak to the caller.
            </div>
          ) : loadingDetail && !detail ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : detail ? (
            <>
              <div className="shrink-0 px-6 py-3 border-b border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-between gap-3 flex-wrap">
                <div>
                  <h2 className="text-sm font-bold text-gray-900 dark:text-white">
                    {detail.sender_name || detail.sender_id}
                  </h2>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 font-mono">{detail.sender_id}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleToggleHumanOnly}
                    className={`text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors ${
                      detail.human_only
                        ? "bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300"
                        : "bg-gray-50 dark:bg-slate-700 border-gray-200 dark:border-slate-600 text-gray-600 dark:text-gray-300"
                    }`}
                  >
                    {detail.human_only ? "Human only (on)" : "Mute AI — human only"}
                  </button>
                  <Link
                    href={`/tickets/${detail.id}`}
                    className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline px-2"
                  >
                    Open ticket
                  </Link>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-2xl mx-auto rounded-xl border border-teal-100 dark:border-teal-900/40 bg-teal-50/60 dark:bg-teal-950/20 px-4 py-3 text-[12px] text-teal-900 dark:text-teal-100 mb-4">
                  <p className="font-semibold mb-1">Take this call</p>
                  <p className="text-teal-800/90 dark:text-teal-200/80 leading-relaxed">
                    Type below and press <strong>Send to caller</strong>. If Twilio still has this call open, your message is
                    spoken on their line (same as the ticket reply). Enable <strong>Human only</strong> to stop the AI from
                    answering further speech until you turn it off. Full browser “mic on the call” needs Twilio Client
                    (future upgrade).
                  </p>
                </div>
                <div className="max-w-2xl mx-auto">
                  <ConversationThread messages={detail.messages || []} />
                </div>
              </div>

              <div className="shrink-0 border-t border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                <div className="max-w-2xl mx-auto space-y-2">
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="What should the caller hear?"
                    rows={3}
                    className="w-full rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 text-gray-900 dark:text-white text-sm p-3 outline-none focus:ring-2 focus:ring-indigo-500/30 resize-none"
                  />
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      disabled={sending || !replyText.trim()}
                      onClick={handleSendToCaller}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-40"
                    >
                      {sending ? "Sending…" : "Send to caller"}
                    </button>
                    {detail.escalation_id ? (
                      <button
                        type="button"
                        disabled={resolving || !replyText.trim()}
                        onClick={handleResolve}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-40"
                      >
                        {resolving ? "…" : "Send & resolve escalation"}
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-sm text-gray-500">Could not load call.</div>
          )}
        </section>
      </div>
    </div>
  );
}
