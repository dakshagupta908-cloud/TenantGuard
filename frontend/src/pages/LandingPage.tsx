import React from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheck,
  BookOpenCheck,
  FileText,
  ArrowRight,
  Lock,
  OctagonAlert,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const LandingPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-100 text-indigo-800 text-xs font-semibold mb-6">
          <ShieldCheck className="w-4 h-4" />
          Citation-ID Validated RAG Pipeline
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto">
          Understand Your Housing Rights & Draft{" "}
          <span className="text-indigo-600">Evidence-Grounded</span> Repair
          Notices
        </h1>
        <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto">
          TenantGuard cross-references your housing issue against indexed local
          statutory excerpts, validates cited section IDs against retrieved
          sources, flags missing evidence, and drafts editable demand letters.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            to={user ? "/dashboard" : "/auth?mode=register"}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 shadow-sm transition"
          >
            {user ? "Go to Your Dashboard" : "Start Free Housing Analysis"}
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/sources"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-slate-700 font-semibold border border-slate-300 hover:bg-slate-100 transition"
          >
            Browse Indexed Statutory Library
          </Link>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
            <BookOpenCheck className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            1. Citation-Validated Retrieval
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            Retrieves jurisdiction-specific housing maintenance provisions and
            checks every cited chunk ID against the retrieved candidate set.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-4">
            <OctagonAlert className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            2. Safe Abstention & Evidence Audit
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            If your jurisdiction lacks indexed statutes or retrieval similarity
            is below threshold, TenantGuard abstains rather than guessing.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <FileText className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">
            3. Editable Demand Letters
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            Generates formal landlord repair notices citing only active indexed
            provisions, with full editing, saving, and plain-text/print export.
          </p>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-white py-8">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-slate-400" />
            <span>
              Strict tenant record isolation • PBKDF2-SHA256 & JWT auth •
              Open-source architecture
            </span>
          </div>
          <div>TenantGuard Portfolio Engineering Project</div>
        </div>
      </footer>
    </div>
  );
};
