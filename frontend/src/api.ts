import {
  AnalysisResult,
  Complaint,
  DemandLetter,
  LegalSource,
  TokenResponse,
  User,
} from "./types";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "/api/v1";

function getToken(): string | null {
  return localStorage.getItem("tg_access_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
        ? data.detail.map((e: { msg?: string }) => e.msg).join(", ")
        : "Request failed. Please check your input and try again.";
    throw new Error(detail);
  }
  return data as T;
}

export const api = {
  // Health & Status
  getReadiness: () =>
    request<{
      status: string;
      database_connected: boolean;
      ai_provider: string;
      indexed_sources: number;
      indexed_chunks: number;
    }>("/ready"),

  // Auth
  register: (payload: {
    email: string;
    full_name: string;
    password: string;
    default_jurisdiction: string;
  }) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (payload: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getMe: () => request<User>("/auth/me"),

  updateMe: (payload: {
    full_name?: string;
    default_jurisdiction?: string;
    current_password?: string;
    new_password?: string;
  }) =>
    request<User>("/auth/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteAccount: () =>
    request<void>("/auth/me", {
      method: "DELETE",
    }),

  // Sources
  listJurisdictions: () => request<string[]>("/sources/jurisdictions"),

  listSources: (jurisdiction?: string) =>
    request<LegalSource[]>(
      jurisdiction
        ? `/sources?jurisdiction=${encodeURIComponent(jurisdiction)}`
        : "/sources"
    ),

  ingestSourceText: (payload: {
    jurisdiction: string;
    title: string;
    citation_prefix: string;
    source_url?: string;
    effective_date?: string;
    is_active: boolean;
    superseded_by?: string;
    raw_text: string;
  }) =>
    request<LegalSource>("/sources/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Complaints
  listComplaints: () => request<Complaint[]>("/complaints"),

  createComplaint: (payload: {
    title: string;
    jurisdiction: string;
    category: string;
    description: string;
    property_address?: string;
    landlord_name?: string;
    landlord_contact?: string;
    issue_start_date?: string;
    prior_notice_given: boolean;
    urgency_level: string;
  }) =>
    request<Complaint>("/complaints", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getComplaint: (id: number) => request<Complaint>(`/complaints/${id}`),

  updateComplaint: (id: number, payload: Partial<Complaint>) =>
    request<Complaint>(`/complaints/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteComplaint: (id: number) =>
    request<void>(`/complaints/${id}`, {
      method: "DELETE",
    }),

  analyzeComplaint: (id: number) =>
    request<AnalysisResult>(`/complaints/${id}/analyze`, {
      method: "POST",
    }),

  // Demand Letters
  generateLetter: (payload: {
    complaint_id: number;
    recipient_name?: string;
    property_address?: string;
    requested_remedy?: string;
    response_deadline_days: number;
  }) =>
    request<DemandLetter>("/letters/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateLetter: (
    letterId: number,
    payload: {
      title?: string;
      recipient_name?: string;
      property_address?: string;
      requested_remedy?: string;
      response_deadline_days?: number;
      content: string;
    }
  ) =>
    request<DemandLetter>(`/letters/${letterId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  sendLetter: (
    letterId: number,
    payload: { recipient_email: string; recipient_phone: string }
  ) =>
    request<{
      email: { sent: boolean; error?: string | null };
      sms: { sent: boolean; error?: string | null };
    }>(`/letters/${letterId}/send`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteLetter: (letterId: number) =>
    request<void>(`/letters/${letterId}`, {
      method: "DELETE",
    }),
};
