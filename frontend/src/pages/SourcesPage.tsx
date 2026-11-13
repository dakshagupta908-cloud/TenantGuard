import React, { useEffect, useState } from "react";
import { BookOpen, PlusCircle, CheckCircle2, AlertTriangle } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { LegalSource } from "../types";

export const SourcesPage: React.FC = () => {
  const { user } = useAuth();
  const [sources, setSources] = useState<LegalSource[]>([]);
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>("");
  const [showIngestForm, setShowIngestForm] = useState(false);

  const [jurisdiction, setJurisdiction] = useState("US-NY-NYC");
  const [title, setTitle] = useState("");
  const [citationPrefix, setCitationPrefix] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadSources = async (jur?: string) => {
    const data = await api.listSources(jur || undefined);
    setSources(data);
  };

  useEffect(() => {
    loadSources(selectedJurisdiction);
  }, [selectedJurisdiction]);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.ingestSourceText({
        jurisdiction,
        title,
        citation_prefix: citationPrefix,
        source_url: sourceUrl || undefined,
        is_active: true,
        raw_text: rawText,
      });
      setTitle("");
      setCitationPrefix("");
      setRawText("");
      setShowIngestForm(false);
      await loadSources(selectedJurisdiction);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to ingest source.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-indigo-600" />
            Indexed Statutory Library (Sample Corpus)
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            TenantGuard only cites statutory sections indexed in this database.
            Default seed entries are sample summaries for demonstration—verify
            against official government publications before legal use.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            aria-label="Filter by jurisdiction"
            value={selectedJurisdiction}
            onChange={(e) => setSelectedJurisdiction(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-xs bg-white font-medium"
          >
            <option value="">All Jurisdictions</option>
            <option value="US-NY-NYC">US-NY-NYC</option>
            <option value="US-CA">US-CA</option>
            <option value="IN-KA-BLR">IN-KA-BLR</option>
          </select>

          {user?.is_admin && (
            <button
              onClick={() => setShowIngestForm(!showIngestForm)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700"
            >
              <PlusCircle className="w-4 h-4" />
              Admin: Ingest Statutory Text
            </button>
          )}
        </div>
      </div>

      {showIngestForm && user?.is_admin && (
        <form
          onSubmit={handleIngest}
          className="bg-white rounded-xl border border-indigo-200 p-6 shadow-sm space-y-4"
        >
          <h2 className="text-base font-bold text-slate-900">
            Admin Ingestion: Add & Vector-Index New Housing Regulations
          </h2>
          {error && (
            <div className="p-3 rounded bg-red-50 text-xs text-red-700">
              {error}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Jurisdiction Code
              </label>
              <input
                type="text"
                required
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                placeholder="US-NY-NYC"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Statute Title
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Municipal Sanitary Code"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Citation Prefix
              </label>
              <input
                type="text"
                required
                value={citationPrefix}
                onChange={(e) => setCitationPrefix(e.target.value)}
                placeholder="Mun. Code"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Official Source URL (Optional)
            </label>
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Raw Statutory Text (Format sections like: § 101: Heading ... text)
            </label>
            <textarea
              rows={5}
              required
              minLength={30}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="§ 101: Lead Paint Disclosure&#10;Every lessor shall disclose known lead-based paint hazards..."
              className="w-full rounded-lg border border-slate-300 p-3 text-xs font-mono"
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowIngestForm(false)}
              className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold"
            >
              {submitting ? "Chunking & Indexing..." : "Chunk & Index Statute"}
            </button>
          </div>
        </form>
      )}

      <div className="space-y-6">
        {sources.map((src) => (
          <div
            key={src.id}
            className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-indigo-50 text-indigo-700 mr-2">
                  {src.jurisdiction}
                </span>
                <span className="text-base font-bold text-slate-900">
                  {src.title}
                </span>
              </div>
              <span className="text-xs text-slate-500">
                {src.chunks.length} Indexed Sections
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {src.chunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className={`p-4 rounded-lg border text-xs space-y-1.5 ${
                    chunk.is_active
                      ? "bg-slate-50 border-slate-200"
                      : "bg-amber-50 border-amber-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-indigo-900">
                      {src.citation_prefix} {chunk.section_code}
                    </span>
                    {chunk.is_active ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-amber-800 font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Superseded
                      </span>
                    )}
                  </div>
                  <div className="font-semibold text-slate-900">
                    {chunk.heading}
                  </div>
                  <p className="text-slate-600 leading-relaxed">
                    {chunk.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
