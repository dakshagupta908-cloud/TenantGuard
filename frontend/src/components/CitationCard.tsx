import React from "react";
import { CheckCircle2, AlertTriangle, ExternalLink } from "lucide-react";
import { VerifiedCitationItem } from "../types";

export const CitationCard: React.FC<{ citation: VerifiedCitationItem }> = ({
  citation,
}) => {
  return (
    <div
      className={`rounded-lg border p-4 transition ${
        citation.is_active
          ? "bg-white border-slate-200"
          : "bg-amber-50/70 border-amber-300"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
              {citation.citation_label}
            </span>
            {citation.is_active ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Indexed Active Provision
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-800 bg-amber-100 px-2 py-0.5 rounded">
                <AlertTriangle className="w-3.5 h-3.5" />
                Superseded / Historical
              </span>
            )}
          </div>
          <h4 className="font-semibold text-slate-900 mt-1">
            {citation.heading}
          </h4>
          <p className="text-xs text-slate-500">{citation.source_title}</p>
        </div>

        <div className="text-right">
          <span className="text-xs font-medium text-slate-500">
            Similarity:{" "}
            <strong className="text-slate-800">
              {(citation.similarity_score * 100).toFixed(0)}%
            </strong>
          </span>
        </div>
      </div>

      {!citation.is_active && citation.superseded_by && (
        <div className="mb-2 text-xs text-amber-900 bg-amber-100/80 px-3 py-1.5 rounded border border-amber-200">
          <strong>Outdated Provision Notice:</strong> Superseded by{" "}
          {citation.superseded_by}. Excluded from formal demand letter citations.
        </div>
      )}

      <blockquote className="text-sm text-slate-700 border-l-2 border-indigo-400 pl-3 italic my-2">
        "{citation.excerpt}"
      </blockquote>

      {citation.source_url && (
        <div className="mt-2">
          <a
            href={citation.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-800"
          >
            View Reference Source URL
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      )}
    </div>
  );
};
