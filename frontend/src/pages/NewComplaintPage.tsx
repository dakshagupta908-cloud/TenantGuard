import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export const NewComplaintPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [jurisdictions, setJurisdictions] = useState<string[]>([
    "US-NY-NYC",
    "US-CA",
    "IN-KA-BLR",
  ]);
  const [title, setTitle] = useState("");
  const [jurisdiction, setJurisdiction] = useState(
    user?.default_jurisdiction || "US-NY-NYC"
  );
  const [category, setCategory] = useState("Heat & Hot Water");
  const [description, setDescription] = useState("");
  const [propertyAddress, setPropertyAddress] = useState("");
  const [landlordName, setLandlordName] = useState("");
  const [landlordContact, setLandlordContact] = useState("");
  const [issueStartDate, setIssueStartDate] = useState("");
  const [priorNoticeGiven, setPriorNoticeGiven] = useState(false);
  const [urgencyLevel, setUrgencyLevel] = useState("high");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listJurisdictions()
      .then((list) => {
        if (list.length > 0) {
          setJurisdictions(list);
        }
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const created = await api.createComplaint({
        title,
        jurisdiction,
        category,
        description,
        property_address: propertyAddress || undefined,
        landlord_name: landlordName || undefined,
        landlord_contact: landlordContact || undefined,
        issue_start_date: issueStartDate || undefined,
        prior_notice_given: priorNoticeGiven,
        urgency_level: urgencyLevel,
      });
      await api.analyzeComplaint(created.id);
      navigate(`/complaints/${created.id}`);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Could not submit complaint."
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Describe Your Housing Problem
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Provide accurate factual details. TenantGuard will retrieve matching
          regulations for your jurisdiction and identify any missing evidence.
        </p>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="jurisdiction"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Jurisdiction
              </label>
              <select
                id="jurisdiction"
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                {jurisdictions.map((j) => (
                  <option key={j} value={j}>
                    {j}
                  </option>
                ))}
                <option value="OTHER-UNINDEXED">
                  Other / Unindexed Jurisdiction (Test Abstention)
                </option>
              </select>
            </div>

            <div>
              <label
                htmlFor="category"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Issue Category
              </label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                <option value="Heat & Hot Water">Heat & Hot Water</option>
                <option value="Water Leaks & Mold">Water Leaks & Mold</option>
                <option value="Plumbing & Structural Repairs">
                  Plumbing & Structural Repairs
                </option>
                <option value="Essential Utility Cut-Off">
                  Essential Utility Cut-Off
                </option>
                <option value="General Habitability">
                  General Habitability
                </option>
              </select>
            </div>
          </div>

          <div>
            <label
              htmlFor="title"
              className="block text-xs font-semibold text-slate-700 mb-1"
            >
              Short Summary Title
            </label>
            <input
              id="title"
              type="text"
              required
              minLength={5}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., No heat in bedroom and indoor temperature at 54°F"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label
              htmlFor="description"
              className="block text-xs font-semibold text-slate-700 mb-1"
            >
              Detailed Factual Description (minimum 20 characters)
            </label>
            <textarea
              id="description"
              rows={4}
              required
              minLength={20}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what is broken, any indoor temperature readings or water damage, how it affects your living conditions, and any conversations with the landlord..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="propertyAddress"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Rental Property Address & Unit
              </label>
              <input
                id="propertyAddress"
                type="text"
                value={propertyAddress}
                onChange={(e) => setPropertyAddress(e.target.value)}
                placeholder="123 West 80th St, Apt 3C"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label
                htmlFor="issueStartDate"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Date Issue Started
              </label>
              <input
                id="issueStartDate"
                type="date"
                value={issueStartDate}
                onChange={(e) => setIssueStartDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="landlordName"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Landlord or Management Name
              </label>
              <input
                id="landlordName"
                type="text"
                value={landlordName}
                onChange={(e) => setLandlordName(e.target.value)}
                placeholder="Apex Property Management"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label
                htmlFor="urgencyLevel"
                className="block text-xs font-semibold text-slate-700 mb-1"
              >
                Urgency Level
              </label>
              <select
                id="urgencyLevel"
                value={urgencyLevel}
                onChange={(e) => setUrgencyLevel(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="emergency">Emergency (Health/Safety)</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              id="priorNoticeGiven"
              type="checkbox"
              checked={priorNoticeGiven}
              onChange={(e) => setPriorNoticeGiven(e.target.checked)}
              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label
              htmlFor="priorNoticeGiven"
              className="text-xs font-medium text-slate-700"
            >
              I have already notified the landlord or property manager about
              this issue
            </label>
          </div>

          <div className="pt-3 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="px-4 py-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {submitting
                ? "Retrieving Statutes & Analyzing..."
                : "Save & Run Statutory Analysis"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
