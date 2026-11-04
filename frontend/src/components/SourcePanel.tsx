"use client";

import { useEffect, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { FileText, LockKeyhole, X } from "lucide-react";
import type { ChatReference } from "@/lib/types";

interface SourcePanelProps {
  source: ChatReference | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function SourceDetails({ source }: { source: ChatReference | null }) {
  if (!source) {
    return (
      <div className="flex flex-1 items-center justify-center p-6 text-center">
        <p className="max-w-[15rem] text-sm leading-6 text-slate-500">
          Sélectionnez une citation dans une réponse pour consulter la source.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5 overflow-y-auto p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-navy-900">
          <FileText aria-hidden="true" size={19} />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Source [{source.n}]
          </p>
          <h3 className="mt-1 break-words text-base font-semibold leading-6 text-navy-900">
            {source.title}
          </h3>
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-slate-200 p-3">
          <dt className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Version
          </dt>
          <dd className="mt-1 text-sm font-medium text-slate-800">
            {source.version}
          </dd>
        </div>
        <div className="rounded-lg border border-slate-200 p-3">
          <dt className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Page
          </dt>
          <dd className="mt-1 text-sm font-medium text-slate-800">
            {source.page}
          </dd>
        </div>
      </dl>

      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Niveau d’accès
        </h4>
        <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700">
          <LockKeyhole aria-hidden="true" size={14} />
          {source.access_level === "conformite"
            ? "Conformité"
            : "Public"}
        </div>
      </div>

      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Extrait
        </h4>
        <blockquote className="mt-2 rounded-lg border-l-2 border-institutional-green bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
          {source.excerpt}
        </blockquote>
      </div>

      <p className="break-all text-[11px] text-slate-400">
        Identifiant fictif : {source.doc_id}
      </p>
    </div>
  );
}

export function SourcePanel({
  source,
  open,
  onOpenChange,
}: SourcePanelProps) {
  const [isDesktop, setIsDesktop] = useState<boolean | null>(null);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(min-width: 1280px)");
    const updateViewport = () => setIsDesktop(mediaQuery.matches);
    updateViewport();
    mediaQuery.addEventListener("change", updateViewport);
    return () => mediaQuery.removeEventListener("change", updateViewport);
  }, []);

  return (
    <>
      {open && isDesktop === true && (
        <aside
          aria-label="Détail de la source"
          className="hidden w-80 shrink-0 flex-col border-l border-slate-200 bg-white xl:flex"
        >
          <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 px-5">
            <h2 className="text-sm font-semibold text-navy-900">Source</h2>
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              aria-label="Rétracter le panneau des sources"
              className="inline-flex h-9 w-9 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
            >
              <X aria-hidden="true" size={17} />
            </button>
          </div>
          <SourceDetails source={source} />
        </aside>
      )}

      <Dialog.Root
        open={open && isDesktop === false}
        onOpenChange={onOpenChange}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-navy-950/40 xl:hidden" />
          <Dialog.Content className="fixed inset-y-0 right-0 z-50 flex w-[min(24rem,92vw)] flex-col bg-white shadow-xl focus:outline-none xl:hidden">
            <div className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 px-5">
              <Dialog.Title className="text-sm font-semibold text-navy-900">
                Source
              </Dialog.Title>
              <Dialog.Close asChild>
                <button
                  type="button"
                  aria-label="Fermer le panneau des sources"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
                >
                  <X aria-hidden="true" size={17} />
                </button>
              </Dialog.Close>
            </div>
            <SourceDetails source={source} />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
