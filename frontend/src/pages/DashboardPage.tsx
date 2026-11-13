import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FilePlus,
  FolderOpen,
  Trash2,
  ArrowRight,
  CheckCircle,
  Clock,
  AlertCircle,
} from "lucide-react";
import { api } from "../api";
import { Complaint } from "../types";

export const DashboardPage: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadComplaints = async () => {
    setLoading(true);
    try {
      const data = await api.listComplaints();
      setComplaints(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load complaints."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaints();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this complaint and all associated drafts?")) {
      return;
    }
    try {
      await api.deleteComplaint(id);
      setComplaints((prev) => prev.filter((c) => c.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Delete failed.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Your Housing Cases & Drafts
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Manage your reported housing conditions, statutory analyses, and
            saved demand letters.
          </p>
        </div>

        <Link
          to="/complaints/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition self-start"
        >
          <FilePlus className="w-4 h-4" />
          New Housing Issue
        </Link>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-sm text-slate-500">
          Loading your saved records...
        </div>
      ) : complaints.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <FolderOpen className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-900">
            No housing complaints recorded yet
          </h3>
          <p className="text-sm text-slate-600 max-w-md mx-auto mt-1">
            Describe a repair issue such as lack of heat, hot water failure,
            water leaks, or utility shutoffs to retrieve relevant statutes and
            draft a formal notice.
          </p>
          <Link
            to="/complaints/new"
            className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700"
          >
            <FilePlus className="w-4 h-4" />
            Create Your First Complaint
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {complaints.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-indigo-300 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded bg-slate-100 text-slate-800">
                    {c.jurisdiction}
                  </span>
                  <span className="text-xs font-medium px-2.5 py-0.5 rounded bg-indigo-50 text-indigo-700">
                    {c.category}
                  </span>
                  {c.status === "letter_ready" ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Letter Drafted ({c.letters.length})
                    </span>
                  ) : c.status === "analyzed" ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Statutes Analyzed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                      <Clock className="w-3.5 h-3.5" />
                      Draft
                    </span>
                  )}
                </div>

                <Link
                  to={`/complaints/${c.id}`}
                  className="block text-lg font-bold text-slate-900 hover:text-indigo-600"
                >
                  {c.title}
                </Link>
                <p className="text-sm text-slate-600 line-clamp-2">
                  {c.description}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/complaints/${c.id}`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition"
                >
                  Open Workspace
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <button
                  onClick={() => handleDelete(c.id)}
                  className="p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition"
                  title="Delete complaint"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
