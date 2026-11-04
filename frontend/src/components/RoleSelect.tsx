"use client";

import { useId } from "react";
import { ShieldCheck } from "lucide-react";
import type { UserRole } from "@/lib/types";

interface RoleSelectProps {
  value: UserRole;
  onChange: (role: UserRole) => void;
}

export function RoleSelect({ value, onChange }: RoleSelectProps) {
  const selectId = useId();

  function handleChange(selectedRole: string) {
    if (selectedRole === "agent" || selectedRole === "conformite") {
      onChange(selectedRole);
    }
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label
          htmlFor={selectId}
          className="text-xs font-medium text-slate-700"
        >
          Rôle
        </label>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
          Mode démo
        </span>
      </div>
      <div className="relative">
        <select
          id={selectId}
          value={value}
          onChange={(event) => handleChange(event.target.value)}
          className="min-h-10 w-full appearance-none rounded-lg border border-slate-200 bg-slate-50 px-3 pr-9 text-sm text-navy-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
        >
          <option value="agent">Agent</option>
          <option value="conformite">Conformité</option>
        </select>
        <ShieldCheck
          aria-hidden="true"
          size={16}
          className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500"
        />
      </div>
      <p className="mt-2 text-[10px] leading-4 text-slate-500">
        Ce choix de démonstration ne remplace pas le rôle issu de l’authentification.
      </p>
    </div>
  );
}
