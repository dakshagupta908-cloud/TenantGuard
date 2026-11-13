import React from "react";
import { ShieldAlert } from "lucide-react";

export const LegalDisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-900 no-print">
      <div className="max-w-7xl mx-auto flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
        <span>
          <strong>Legal Information Only:</strong> TenantGuard is an automated
          statutory research and letter-drafting tool. It is not a law firm,
          does not provide legal advice, and only cites retrieved provisions in
          its indexed statutory database. Always verify current official statutes
          for your jurisdiction.
        </span>
      </div>
    </div>
  );
};
