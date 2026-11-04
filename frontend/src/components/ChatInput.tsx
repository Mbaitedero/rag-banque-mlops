"use client";

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUp, LoaderCircle } from "lucide-react";

interface ChatInputProps {
  disabled?: boolean;
  onSend: (question: string) => void | Promise<void>;
}

export function ChatInput({ disabled = false, onSend }: ChatInputProps) {
  const [question, setQuestion] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [question]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (disabled || !trimmedQuestion) return;
    setQuestion("");
    void onSend(trimmedQuestion);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto w-full max-w-4xl">
      <label htmlFor="chat-question" className="sr-only">
        Votre question
      </label>
      <div className="flex items-end gap-3 rounded-xl border border-slate-300 bg-white p-2 shadow-sm transition-colors focus-within:border-slate-400">
        <textarea
          ref={textareaRef}
          id="chat-question"
          rows={1}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Posez une question sur les documents…"
          className="max-h-[180px] min-h-10 flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm leading-6 text-navy-900 placeholder:text-slate-400 focus:outline-none focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={disabled || question.trim().length === 0}
          aria-label={disabled ? "Réponse en cours" : "Envoyer la question"}
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-navy-900 text-white transition-colors hover:bg-navy-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {disabled ? (
            <LoaderCircle aria-hidden="true" size={18} className="animate-spin" />
          ) : (
            <ArrowUp aria-hidden="true" size={19} />
          )}
        </button>
      </div>
      <p className="mt-2 text-center text-[11px] leading-4 text-slate-500">
        Entrée pour envoyer · Maj+Entrée pour un retour à la ligne
      </p>
    </form>
  );
}
