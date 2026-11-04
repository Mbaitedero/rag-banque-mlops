import {
  FileText,
  LockKeyhole,
  MessageSquareText,
  PanelRight,
} from "lucide-react";
import { ChatMessage, type ChatMessageData } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import type { ChatReference, UserRole } from "@/lib/types";

interface ChatAreaProps {
  messages: ChatMessageData[];
  isSending: boolean;
  sourcesOpen: boolean;
  role: UserRole;
  displayName: string;
  onDisplayNameChange: (name: string) => void;
  feedbackNotice?: string | null;
  onCitation?: (reference: ChatReference) => void;
  onSend: (question: string) => void | Promise<void>;
  onToggleSources: () => void;
  onFeedback?: (requestId: string, rating: "up" | "down") => void;
}

export function ChatArea({
  messages,
  isSending,
  sourcesOpen,
  role,
  displayName,
  onDisplayNameChange,
  feedbackNotice,
  onCitation,
  onSend,
  onToggleSources,
  onFeedback,
}: ChatAreaProps) {
  return (
    <main className="flex min-h-0 flex-1 flex-col bg-institutional-gray">
      <header className="flex min-h-16 items-center justify-between border-b border-slate-200 bg-white px-5 sm:px-8">
        <div className="pl-11 sm:pl-0">
          <h1 className="text-sm font-semibold text-navy-900">
            Assistant documentaire
          </h1>
          <p className="mt-0.5 text-xs text-slate-500">
            MBAITEDERO BANK <span aria-hidden="true">·</span> environnement de
            démonstration
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="hidden items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-800 sm:inline-flex">
            <span
              aria-hidden="true"
              className="h-1.5 w-1.5 rounded-full bg-institutional-green"
            />
            Documents fictifs
          </span>
          <button
            type="button"
            onClick={onToggleSources}
            className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green sm:px-3"
            aria-label="Ouvrir ou rétracter le panneau des sources"
            aria-expanded={sourcesOpen}
          >
            <PanelRight aria-hidden="true" size={16} />
            <span className="hidden sm:inline">Sources</span>
          </button>
        </div>
      </header>

      <section
        aria-label="Conversation"
        className="flex min-h-0 flex-1 flex-col overflow-y-auto"
      >
        {messages.length === 0 ? (
          <div className="m-auto w-full max-w-2xl px-6 py-12">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-navy-900 text-white shadow-sm">
              <MessageSquareText aria-hidden="true" size={23} />
            </div>
            <h2 className="mt-5 text-center text-2xl font-semibold tracking-tight text-navy-900">
              Bonjour{displayName.trim() ? `, ${displayName.trim()}` : ""} !
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-center text-sm leading-6 text-slate-600">
              Je suis l’assistant documentaire de MBAITEDERO BANK, une banque
              fictive. Posez une question sur les documents de démonstration :
              je vous répondrai avec courtoisie à partir des sources autorisées
              pour le rôle démo « {role === "agent" ? "Agent" : "Conformité"} ».
            </p>

            <div className="mx-auto mt-5 flex max-w-sm items-center gap-2">
              <label
                htmlFor="display-name"
                className="shrink-0 text-xs font-medium text-slate-600"
              >
                Votre prénom
              </label>
              <input
                id="display-name"
                value={displayName}
                onChange={(event) =>
                  onDisplayNameChange(event.target.value.slice(0, 40))
                }
                maxLength={40}
                placeholder="Facultatif"
                autoComplete="off"
                className="min-h-9 min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 text-sm text-navy-900 placeholder:text-slate-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
              />
            </div>
            <p className="mt-1 text-center text-[11px] text-slate-500">
              Prénom d’affichage facultatif : il reste dans cette page et n’est
              pas transmis au serveur.
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                disabled={isSending}
                onClick={() =>
                  onSend(
                    "Quel est le plafond de retrait de la carte Premium ?",
                  )
                }
                className="rounded-xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <FileText
                  aria-hidden="true"
                  className="text-institutional-green"
                  size={18}
                />
                <h3 className="mt-3 text-sm font-semibold text-navy-900">
                  Question suggérée
                </h3>
                <p className="mt-1 text-xs leading-5 text-slate-600">
                  Quel est le plafond de retrait de la carte Premium ?
                </p>
              </button>
              <button
                type="button"
                disabled={isSending}
                onClick={() =>
                  onSend("Quelle est la procédure KYC renforcée ?")
                }
                className="rounded-xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <LockKeyhole
                  aria-hidden="true"
                  className="text-institutional-green"
                  size={18}
                />
                <h3 className="mt-3 text-sm font-semibold text-navy-900">
                  Question avec accès contrôlé
                </h3>
                <p className="mt-1 text-xs leading-5 text-slate-600">
                  Quelle est la procédure KYC renforcée ?
                </p>
              </button>
            </div>
          </div>
        ) : (
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-5 px-5 py-8 sm:px-8">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                references={message.references}
                onCitation={onCitation}
                onFeedback={onFeedback}
              />
            ))}
            {isSending && (
              <p role="status" className="sr-only">
                L’assistant prépare sa réponse.
              </p>
            )}
          </div>
        )}
      </section>

      <div className="border-t border-slate-200 bg-white px-5 py-4 sm:px-8">
        <div className="mx-auto max-w-4xl">
          {feedbackNotice && (
            <p
              role={
                feedbackNotice.startsWith("Le retour n’a pas pu être envoyé")
                  ? "alert"
                  : "status"
              }
              className="mb-3 text-center text-xs text-slate-600"
            >
              {feedbackNotice}
            </p>
          )}
          <ChatInput disabled={isSending} onSend={onSend} />
          <p className="mt-2 text-center text-[11px] leading-4 text-slate-500">
            Démonstration avec des données fictives. Vérifiez les sources avant
            toute utilisation.
          </p>
        </div>
      </div>
    </main>
  );
}
