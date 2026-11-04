"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy, ThumbsDown, ThumbsUp } from "lucide-react";
import type { ChatReference, ChatResponse } from "@/lib/types";

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  error?: boolean;
  references?: ChatReference[];
  response?: ChatResponse;
}

interface ChatMessageProps {
  message: ChatMessageData;
  references?: ChatReference[];
  onCitation?: (reference: ChatReference) => void;
  onFeedback?: (requestId: string, rating: "up" | "down") => void;
}

function linkifyCitations(content: string): string {
  const markdownCode = /(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`]*`)/g;
  return content
    .split(markdownCode)
    .map((part, index) => {
      if (index % 2 === 1) return part;
      return part.replace(
        /\[(\d+)\](?!\()/g,
        "[$1](https://citation.invalid/$1)",
      );
    })
    .join("");
}

export function ChatMessage({
  message,
  references = message.response?.references ?? [],
  onCitation,
  onFeedback,
}: ChatMessageProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">(
    "idle",
  );
  const isUser = message.role === "user";
  const isAccessDenied = message.response?.reason === "acces_refuse";
  const isError = message.error || message.response?.reason === "erreur";
  const isRefusal = message.response?.refused && !isAccessDenied && !isError;
  const requestId = message.response?.request_id;
  const canSendFeedback = Boolean(requestId && onFeedback);

  async function copyMessage() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }

  if (isUser) {
    return (
      <article
        aria-label="Votre message"
        className="flex justify-end"
        data-message-id={message.id}
      >
        <p className="max-w-[min(82%,42rem)] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-navy-900 px-5 py-3.5 text-sm leading-6 text-white shadow-sm">
          {message.content}
        </p>
      </article>
    );
  }

  return (
    <article
      aria-label="Réponse de l’assistant"
      className="flex justify-start"
      data-message-id={message.id}
    >
      <div className="w-full max-w-3xl rounded-2xl rounded-bl-md border border-slate-200 bg-white px-5 py-4 shadow-sm sm:px-6">
        {isAccessDenied && (
          <div
            role="status"
            className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-sm font-medium text-amber-950"
          >
            Accès refusé — cette information n’est pas accessible avec le rôle
            actuel.
          </div>
        )}
        {isRefusal && (
          <div
            role="status"
            className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-sm font-medium text-amber-950"
          >
            Réponse non disponible à partir des sources.
          </div>
        )}
        {isError && (
          <div
            role="alert"
            className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm font-medium text-red-900"
          >
            {message.content ||
              "Une erreur est survenue pendant le traitement de cette demande."}
          </div>
        )}

        {!isError && <div className="space-y-3 break-words text-sm leading-7 text-slate-800 [&_a:not([data-citation])]:font-medium [&_a:not([data-citation])]:text-institutional-green [&_a:not([data-citation])]:underline [&_blockquote]:border-l-2 [&_blockquote]:border-slate-300 [&_blockquote]:pl-4 [&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1 [&_code]:py-0.5 [&_h1]:text-lg [&_h1]:font-semibold [&_h2]:text-base [&_h2]:font-semibold [&_li]:ml-5 [&_ol]:list-decimal [&_p]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-slate-100 [&_pre]:p-3 [&_table]:w-full [&_td]:border [&_td]:border-slate-200 [&_td]:px-2 [&_td]:py-1 [&_th]:border [&_th]:border-slate-200 [&_th]:bg-slate-50 [&_th]:px-2 [&_th]:py-1 [&_ul]:list-disc">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children, ...props }) => {
                const citationMatch = href?.match(
                  /^https:\/\/citation\.invalid\/(\d+)$/,
                );
                if (citationMatch) {
                  const reference = references.find(
                    (item) => item.n === Number(citationMatch[1]),
                  );
                  if (reference) {
                    return (
                      <button
                        type="button"
                        data-citation
                        disabled={!onCitation}
                        onClick={() => onCitation?.(reference)}
                        aria-label={`Ouvrir la source ${reference.n} : ${reference.title}`}
                        className="mx-0.5 inline-flex min-h-6 min-w-6 items-center justify-center rounded-full border border-emerald-200 bg-emerald-50 px-1.5 align-middle text-xs font-semibold leading-none text-emerald-800 transition-colors hover:bg-emerald-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 disabled:cursor-default disabled:opacity-70"
                      >
                        {children}
                      </button>
                    );
                  }
                  return (
                    <span className="font-medium text-slate-500">
                      {children}
                    </span>
                  );
                }

                return (
                  <a
                    href={href}
                    {...props}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {children}
                  </a>
                );
              },
            }}
          >
            {linkifyCitations(message.content)}
          </ReactMarkdown>
        </div>}

        {requestId && (
          <div className="mt-4 flex flex-wrap items-center gap-1 border-t border-slate-100 pt-3">
            <button
              type="button"
              onClick={copyMessage}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-navy-900"
              aria-label="Copier la réponse"
            >
              {copyState === "copied" ? (
                <Check aria-hidden="true" size={15} />
              ) : (
                <Copy aria-hidden="true" size={15} />
              )}
              {copyState === "copied"
                ? "Copié"
                : copyState === "error"
                  ? "Copie impossible"
                  : "Copier"}
            </button>
            <span className="sr-only" aria-live="polite">
              {copyState === "copied"
                ? "Réponse copiée."
                : copyState === "error"
                  ? "La copie a échoué."
                  : ""}
            </span>
            <button
              type="button"
              disabled={!canSendFeedback}
              onClick={() => {
                if (requestId && onFeedback) onFeedback(requestId, "up");
              }}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-navy-900 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Réponse utile"
              title={canSendFeedback ? "Réponse utile" : "Retour bientôt disponible"}
            >
              <ThumbsUp aria-hidden="true" size={15} />
              Utile
            </button>
            <button
              type="button"
              disabled={!canSendFeedback}
              onClick={() => {
                if (requestId && onFeedback) onFeedback(requestId, "down");
              }}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-navy-900 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Réponse non utile"
              title={canSendFeedback ? "Réponse non utile" : "Retour bientôt disponible"}
            >
              <ThumbsDown aria-hidden="true" size={15} />
              À améliorer
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
