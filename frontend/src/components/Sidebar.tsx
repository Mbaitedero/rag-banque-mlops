"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { BookOpen, Clock3, Menu, Plus, X } from "lucide-react";
import { useId, useState } from "react";
import { RoleSelect } from "@/components/RoleSelect";
import type { UserRole } from "@/lib/types";

export interface ConversationSummary {
  id: string;
  title: string;
}

interface SidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  role: UserRole;
  displayName: string;
  onDisplayNameChange: (name: string) => void;
  onRoleChange: (role: UserRole) => void;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
}

function SidebarContent({
  conversations,
  activeConversationId,
  role,
  displayName,
  onDisplayNameChange,
  onRoleChange,
  onNewConversation,
  onSelectConversation,
}: SidebarProps) {
  const displayNameId = useId();

  return (
    <>
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-200 px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy-900 text-white">
          <BookOpen aria-hidden="true" size={19} />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-wide text-navy-900">
            MBAITEDERO BANK
          </p>
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
            Banque fictive
          </p>
        </div>
      </div>

      <div className="shrink-0 p-4">
        <button
          type="button"
          onClick={onNewConversation}
          className="flex min-h-10 w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-navy-900 transition-colors hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
        >
          <Plus aria-hidden="true" size={16} />
          Nouvelle conversation
        </button>
      </div>

      <nav
        aria-label="Historique des conversations"
        className="min-h-0 flex-1 overflow-y-auto px-4"
      >
        <div className="flex items-center gap-2 px-1 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <Clock3 aria-hidden="true" size={14} />
          Historique
        </div>
        {conversations.length === 0 ? (
          <p className="px-1 py-3 text-xs leading-5 text-slate-500">
            Vos conversations apparaîtront ici.
          </p>
        ) : (
          <ul className="space-y-1">
            {conversations.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  onClick={() => onSelectConversation(conversation.id)}
                  aria-current={
                    conversation.id === activeConversationId ? "page" : undefined
                  }
                  className="w-full truncate rounded-lg px-3 py-2.5 text-left text-sm text-slate-700 transition-colors hover:bg-slate-100 aria-[current=page]:bg-slate-100 aria-[current=page]:font-medium aria-[current=page]:text-navy-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
                  title={conversation.title}
                >
                  {conversation.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div className="shrink-0 space-y-4 border-t border-slate-200 p-4">
        <div>
          <label
            htmlFor={displayNameId}
            className="mb-1.5 block text-xs font-medium text-slate-700"
          >
            Prénom d’affichage
          </label>
          <input
            id={displayNameId}
            value={displayName}
            onChange={(event) =>
              onDisplayNameChange(event.target.value.slice(0, 40))
            }
            maxLength={40}
            autoComplete="off"
            placeholder="Facultatif"
            className="min-h-9 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-navy-900 placeholder:text-slate-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional-green"
          />
          <p className="mt-1 text-[10px] leading-4 text-slate-500">
            Affichage local uniquement, non transmis au serveur.
          </p>
        </div>
        <RoleSelect value={role} onChange={onRoleChange} />
      </div>
    </>
  );
}

export function Sidebar(props: SidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
        <SidebarContent {...props} />
      </aside>

      <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
        <Dialog.Trigger asChild>
          <button
            type="button"
            aria-label="Ouvrir le menu et l’historique"
            className="fixed left-3 top-3 z-20 inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-navy-900 shadow-sm md:hidden"
          >
            <Menu aria-hidden="true" size={19} />
          </button>
        </Dialog.Trigger>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-navy-950/40 md:hidden" />
          <Dialog.Content className="fixed inset-y-0 left-0 z-50 flex w-[min(20rem,88vw)] flex-col bg-white shadow-xl focus:outline-none md:hidden">
            <Dialog.Title className="sr-only">
              Menu de navigation
            </Dialog.Title>
            <div className="absolute right-3 top-3 z-10">
              <Dialog.Close asChild>
                <button
                  type="button"
                  aria-label="Fermer le menu"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100"
                >
                  <X aria-hidden="true" size={18} />
                </button>
              </Dialog.Close>
            </div>
            <SidebarContent
              {...props}
              onNewConversation={() => {
                props.onNewConversation();
                setMobileOpen(false);
              }}
              onSelectConversation={(id) => {
                props.onSelectConversation(id);
                setMobileOpen(false);
              }}
            />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
