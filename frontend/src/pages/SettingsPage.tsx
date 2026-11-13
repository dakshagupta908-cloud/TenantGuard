import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export const SettingsPage: React.FC = () => {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [defaultJurisdiction, setDefaultJurisdiction] = useState(
    user?.default_jurisdiction || "US-NY-NYC"
  );
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<{
    ai_provider: string;
    indexed_sources: number;
    indexed_chunks: number;
  } | null>(null);

  useEffect(() => {
    api
      .getReadiness()
      .then((res) => setSystemStatus(res))
      .catch(() => {});
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await api.updateMe({
        full_name: fullName,
        default_jurisdiction: defaultJurisdiction,
        current_password: newPassword ? currentPassword : undefined,
        new_password: newPassword ? newPassword : undefined,
      });
      setCurrentPassword("");
      setNewPassword("");
      await refreshUser();
      setMessage("Account settings updated.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Update failed.");
    }
  };

  const handleDeleteAccount = async () => {
    if (
      !window.confirm(
        "Permanently delete your account and all saved complaints and demand letters?"
      )
    ) {
      return;
    }
    await api.deleteAccount();
    logout();
    navigate("/");
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-900">Account Settings</h1>
          {user?.is_admin && (
            <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-100 text-indigo-800">
              Administrator Account
            </span>
          )}
        </div>
        {message && (
          <div className="mt-3 p-3 rounded bg-emerald-50 text-xs text-emerald-800">
            {message}
          </div>
        )}
        {error && (
          <div className="mt-3 p-3 rounded bg-red-50 text-xs text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSave} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Default Jurisdiction
            </label>
            <select
              value={defaultJurisdiction}
              onChange={(e) => setDefaultJurisdiction(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
            >
              <option value="US-NY-NYC">US-NY-NYC</option>
              <option value="US-CA">US-CA</option>
              <option value="IN-KA-BLR">IN-KA-BLR</option>
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Current Password (required if changing password)
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required={Boolean(newPassword)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                New Password (minimum 8 characters)
              </label>
              <input
                type="password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700"
          >
            Save Changes
          </button>
        </form>
      </div>

      {systemStatus && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm text-xs space-y-1">
          <h2 className="text-sm font-bold text-slate-900 mb-2">
            RAG Engine & Vector Store Telemetry
          </h2>
          <div>
            <strong>AI Provider Mode:</strong> {systemStatus.ai_provider}
          </div>
          <div>
            <strong>Indexed Statutory Sources:</strong>{" "}
            {systemStatus.indexed_sources}
          </div>
          <div>
            <strong>Indexed Vector Chunks:</strong>{" "}
            {systemStatus.indexed_chunks}
          </div>
        </div>
      )}

      <div className="bg-red-50 rounded-xl border border-red-200 p-6">
        <h2 className="text-sm font-bold text-red-900">Danger Zone</h2>
        <p className="text-xs text-red-700 mt-1 mb-3">
          Deleting your account permanently removes your profile, complaints,
          analyses, and demand letter drafts.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="px-4 py-2 rounded-lg bg-red-600 text-white text-xs font-semibold hover:bg-red-700"
        >
          Delete My Account & Data
        </button>
      </div>
    </div>
  );
};
