export interface User {
  id: number;
  email: string;
  full_name: string;
  default_jurisdiction: string;
  is_admin: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LegalChunk {
  id: number;
  source_id: number;
  jurisdiction: string;
  section_code: string;
  heading: string;
  content: string;
  is_active: boolean;
  superseded_by?: string | null;
}

export interface LegalSource {
  id: number;
  jurisdiction: string;
  title: string;
  citation_prefix: string;
  source_url?: string | null;
  effective_date?: string | null;
  is_active: boolean;
  superseded_by?: string | null;
  created_at: string;
  chunks: LegalChunk[];
}

export interface VerifiedCitationItem {
  chunk_id: number;
  source_id: number;
  jurisdiction: string;
  source_title: string;
  citation_label: string;
  section_code: string;
  heading: string;
  excerpt: string;
  similarity_score: number;
  is_active: boolean;
  superseded_by?: string | null;
  source_url?: string | null;
}

export interface AnalysisResult {
  id: number;
  complaint_id: number;
  abstained: boolean;
  abstention_reason?: string | null;
  confidence_score: number;
  summary_explanation: string;
  key_rights: string[];
  missing_evidence: string[];
  limitations_and_warnings: string[];
  recommended_next_steps: string[];
  verified_citations: VerifiedCitationItem[];
  stripped_hallucinations_count: number;
  created_at: string;
}

export interface DemandLetter {
  id: number;
  complaint_id: number;
  user_id: number;
  title: string;
  recipient_name: string;
  property_address: string;
  requested_remedy: string;
  response_deadline_days: number;
  content: string;
  citations_used: string[];
  created_at: string;
  updated_at: string;
}

export interface Complaint {
  id: number;
  user_id: number;
  title: string;
  jurisdiction: string;
  category: string;
  description: string;
  property_address?: string | null;
  landlord_name?: string | null;
  landlord_contact?: string | null;
  issue_start_date?: string | null;
  prior_notice_given: boolean;
  urgency_level: "low" | "medium" | "high" | "emergency";
  status: "draft" | "analyzed" | "letter_ready" | "resolved";
  created_at: string;
  updated_at: string;
  analyses: AnalysisResult[];
  letters: DemandLetter[];
}
