import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Sparkles,
  FileText,
  Download,
  Printer,
  Send,
  Save,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
} from "lucide-react";
import { api } from "../api";
import { CitationCard } from "../components/CitationCard";
import { Complaint, DemandLetter } from "../types";

export const ComplaintDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const complaintId = Number(id);

  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [activeLetter, setActiveLetter] = useState<DemandLetter | null>(null);
  const [letterContent, setLetterContent] = useState("");
  const [letterDirty, setLetterDirty] = useState(false);
  const [deadlineDays, setDeadlineDays] = useState(14);
  const [requestedRemedy, setRequestedRemedy] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [recipientPhone, setRecipientPhone] = useState("");
  const [initialLoading, setInitialLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadWorkspace = async (options?: {
    isInitial?: boolean;
    preserveUnsavedLetter?: boolean;
  }) => {
    if (options?.isInitial) {
      setInitialLoading(true);
    }
    try {
      const data = await api.getComplaint(complaintId);
      setComplaint(data);
      if (data.letters && data.letters.length > 0) {
        const latestDraft = data.letters[0];
        setActiveLetter(latestDraft);
        if (!options?.preserveUnsavedLetter || !letterDirty) {
          setLetterContent(latestDraft.content);
          setDeadlineDays(latestDraft.response_deadline_days);
          setRequestedRemedy(latestDraft.requested_remedy);
          setLetterDirty(false);
        }
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load complaint."
      );
    } finally {
      if (options?.isInitial) {
        setInitialLoading(false);
      }
    }
  };

  useEffect(() => {
    if (complaintId) {
      loadWorkspace({ isInitial: true });
    }
  }, [complaintId]);

  const handleReanalyze = async () => {
    setWorking(true);
    setStatusMessage(null);
    setError(null);
    try {
      await api.analyzeComplaint(complaintId);
      await loadWorkspace({ preserveUnsavedLetter: true });
      setStatusMessage("Statutory RAG analysis updated.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setWorking(false);
    }
  };

  const handleGenerateLetter = async () => {
    setWorking(true);
    setStatusMessage(null);
    setError(null);
    try {
      const draft = await api.generateLetter({
        complaint_id: complaintId,
        requested_remedy: requestedRemedy || undefined,
        response_deadline_days: deadlineDays,
      });
      setActiveLetter(draft);
      setLetterContent(draft.content);
      setLetterDirty(false);
      await loadWorkspace({ preserveUnsavedLetter: false });
      setStatusMessage(
        "Evidence-grounded demand letter generated from active cited provisions."
      );
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Letter generation failed."
      );
    } finally {
      setWorking(false);
    }
  };

  const handleSaveLetterEdits = async () => {
    if (!activeLetter) return;
    setWorking(true);
    setStatusMessage(null);
    setError(null);
    try {
      const updated = await api.updateLetter(activeLetter.id, {
        content: letterContent,
        response_deadline_days: deadlineDays,
        requested_remedy: requestedRemedy || activeLetter.requested_remedy,
      });
      setActiveLetter(updated);
      setLetterDirty(false);
      setStatusMessage("Letter revisions saved.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not save edits.");
    } finally {
      setWorking(false);
    }
  };

  const handleSendLetter = async () => {
    if (!activeLetter) return;
    if (letterDirty) {
      setError("Save your letter edits before sending the notice.");
      return;
    }
    if (
      !window.confirm(
        `Send this repair notice to ${recipientEmail} by email and ${recipientPhone} by SMS?`
      )
    ) {
      return;
    }

    setWorking(true);
    setStatusMessage(null);
    setError(null);
    try {
      const result = await api.sendLetter(activeLetter.id, {
        recipient_email: recipientEmail,
        recipient_phone: recipientPhone,
      });
      const outcomes = [
        `Email: ${result.email.sent ? "sent" : result.email.error}`,
        `SMS: ${result.sms.sent ? "sent" : result.sms.error}`,
      ];
      if (result.email.sent && result.sms.sent) {
        setStatusMessage(`Repair notice sent. ${outcomes.join(" • ")}`);
      } else {
        setError(`Delivery was incomplete. ${outcomes.join(" • ")}`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not send notice.");
    } finally {
      setWorking(false);
    }
  };

  const handleDownloadTxt = () => {
    if (!activeLetter) return;
    const blob = new Blob([letterContent], {
      type: "text/plain;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tenantguard_repair_notice_${activeLetter.id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (initialLoading) {
    return (
      <div className="max-w-7xl mx-auto p-8 text-center text-sm text-slate-600">
        Loading workspace...
      </div>
    );
  }

  if (!complaint) {
    return (
      <div className="max-w-7xl mx-auto p-8 text-center text-sm text-red-600">
        {error || "Complaint not found."}
      </div>
    );
  }

  const latestAnalysis =
    complaint.analyses && complaint.analyses.length > 0
      ? complaint.analyses[0]
      : null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Summary */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm no-print">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-slate-100 text-slate-800">
                {complaint.jurisdiction}
              </span>
              <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-indigo-50 text-indigo-700">
                {complaint.category}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900">
              {complaint.title}
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              {complaint.description}
            </p>
          </div>

          <button
            onClick={handleReanalyze}
            disabled={working}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {latestAnalysis ? "Re-Run Statutory Analysis" : "Run Analysis"}
          </button>
        </div>

        {statusMessage && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800">
            {statusMessage}
          </div>
        )}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
            {error}
          </div>
        )}
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: RAG Statutory Analysis & Citations */}
        <div className="lg:col-span-6 space-y-6 no-print">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-3">
              Grounded Statutory Analysis
            </h2>

            {!latestAnalysis ? (
              <p className="text-sm text-slate-600">
                No analysis run yet. Click "Run Analysis" above to retrieve
                statutory provisions.
              </p>
            ) : latestAnalysis.abstained ? (
              <div className="p-4 rounded-lg bg-amber-50 border border-amber-300 space-y-2">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Safe Abstention Triggered</span>
                </div>
                <p className="text-xs text-amber-900">
                  {latestAnalysis.abstention_reason}
                </p>
                <p className="text-xs text-slate-700">
                  {latestAnalysis.summary_explanation}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-indigo-50/70 border border-indigo-100 text-sm text-slate-800">
                  {latestAnalysis.summary_explanation}
                </div>

                {latestAnalysis.missing_evidence.length > 0 && (
                  <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5 mb-2">
                      <HelpCircle className="w-4 h-4" />
                      Missing Evidence & Documentation Gaps
                    </h3>
                    <ul className="list-disc list-inside text-xs text-amber-900 space-y-1">
                      {latestAnalysis.missing_evidence.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {latestAnalysis.limitations_and_warnings.length > 0 && (
                  <div className="p-4 rounded-lg bg-slate-100 border border-slate-200">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                      Limitations & Statutory Warnings
                    </h3>
                    <ul className="list-disc list-inside text-xs text-slate-600 space-y-1">
                      {latestAnalysis.limitations_and_warnings.map(
                        (warn, idx) => (
                          <li key={idx}>{warn}</li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                {latestAnalysis.recommended_next_steps.length > 0 && (
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Recommended Next Steps
                    </h3>
                    <ul className="list-decimal list-inside text-xs text-slate-700 space-y-1.5">
                      {latestAnalysis.recommended_next_steps.map(
                        (step, idx) => (
                          <li key={idx}>{step}</li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Citations List */}
          {latestAnalysis && latestAnalysis.verified_citations.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-900">
                Retrieved & Citation-ID Validated Excerpts (
                {latestAnalysis.verified_citations.length})
              </h3>
              {latestAnalysis.verified_citations.map((cit) => (
                <CitationCard key={cit.chunk_id} citation={cit} />
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Editable Demand Letter Generator */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4 no-print">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-600" />
                  Formal Repair Notice & Demand Letter
                </h2>
                <p className="text-xs text-slate-500">
                  Uses only tenant-supplied facts and active indexed citations.
                </p>
              </div>

              <button
                onClick={handleGenerateLetter}
                disabled={working}
                className="px-3.5 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50"
              >
                {activeLetter ? "Regenerate Draft" : "Generate Letter Draft"}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4 no-print">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Requested Remedy
                </label>
                <input
                  type="text"
                  value={requestedRemedy}
                  onChange={(e) => setRequestedRemedy(e.target.value)}
                  placeholder="e.g., Restore heat to at least 68°F and inspect radiator valve"
                  className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Response Deadline (Days)
                </label>
                <input
                  type="number"
                  min={1}
                  max={90}
                  value={deadlineDays}
                  onChange={(e) => setDeadlineDays(Number(e.target.value))}
                  className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs"
                />
              </div>
            </div>

            {activeLetter ? (
              <div className="space-y-4">
                <textarea
                  rows={20}
                  value={letterContent}
                  onChange={(e) => {
                    setLetterContent(e.target.value);
                    setLetterDirty(true);
                  }}
                  aria-label="Editable demand letter content"
                  className="w-full rounded-lg border border-slate-300 p-4 font-mono text-xs leading-relaxed text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />

                <div className="flex flex-wrap items-center justify-between gap-2 no-print">
                  <button
                    onClick={handleSaveLetterEdits}
                    disabled={working}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700"
                  >
                    <Save className="w-4 h-4" />
                    {letterDirty ? "Save Unsaved Revisions*" : "Save Revisions"}
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleDownloadTxt}
                      className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                    >
                      <Download className="w-4 h-4" />
                      Download .TXT
                    </button>
                    <button
                      onClick={() => window.print()}
                      className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                    >
                      <Printer className="w-4 h-4" />
                      Print / Save PDF
                    </button>
                  </div>

                  <div className="space-y-3 rounded-lg border border-indigo-100 bg-indigo-50/50 p-4 no-print">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">
                        Send Repair Notice
                      </h3>
                      <p className="text-xs text-slate-600 mt-1">
                        Sends this saved letter by email and a deadline summary by
                        SMS. Review the recipients and letter before sending.
                      </p>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label
                          htmlFor="notice-email"
                          className="block text-xs font-semibold text-slate-700 mb-1"
                        >
                          Landlord email
                        </label>
                        <input
                          id="notice-email"
                          type="email"
                          required
                          value={recipientEmail}
                          onChange={(event) =>
                            setRecipientEmail(event.target.value)
                          }
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label
                          htmlFor="notice-phone"
                          className="block text-xs font-semibold text-slate-700 mb-1"
                        >
                          Landlord mobile (international format)
                        </label>
                        <input
                          id="notice-phone"
                          type="tel"
                          required
                          pattern="^\+[1-9]\d{7,14}$"
                          placeholder="+14155550123"
                          value={recipientPhone}
                          onChange={(event) =>
                            setRecipientPhone(event.target.value)
                          }
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
                        />
                      </div>
                    </div>
                    <button
                      onClick={handleSendLetter}
                      disabled={working || !recipientEmail || !recipientPhone}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50"
                    >
                      <Send className="w-4 h-4" />
                      {working ? "Sending..." : "Review & Send Email + SMS"}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 rounded-lg border border-dashed border-slate-300 text-center text-xs text-slate-500">
                Click "Generate Letter Draft" above to prepare a customized
                repair notice grounded in your complaint facts and indexed
                statutes.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
