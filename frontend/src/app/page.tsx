"use client";

import { useMemo, useRef, useState } from "react";
import { ChatArea } from "@/components/ChatArea";
import type { ChatMessageData } from "@/components/ChatMessage";
import { Sidebar, type ConversationSummary } from "@/components/Sidebar";
import { SourcePanel } from "@/components/SourcePanel";
import { sendFeedback, sendMessage } from "@/lib/api";
import type {
  ChatReference,
  ChatStreamEvent,
  UserRole,
} from "@/lib/types";

interface Conversation extends ConversationSummary {
  messages: ChatMessageData[];
}

function createId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `conversation-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function updateMessage(
  conversations: Conversation[],
  conversationId: string,
  messageId: string,
  update: (message: ChatMessageData) => ChatMessageData,
): Conversation[] {
  return conversations.map((conversation) =>
    conversation.id !== conversationId
      ? conversation
      : {
          ...conversation,
          messages: conversation.messages.map((message) =>
            message.id === messageId ? update(message) : message,
          ),
        },
  );
}

export default function HomePage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [role, setRole] = useState<UserRole>("agent");
  const [displayName, setDisplayName] = useState("");
  const [isSending, setIsSending] = useState(false);
  const isSendingRef = useRef(false);
  const [selectedSource, setSelectedSource] = useState<ChatReference | null>(
    null,
  );
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(false);
  const [feedbackNotice, setFeedbackNotice] = useState<string | null>(null);

  const activeConversation = useMemo(
    () =>
      conversations.find(
        (conversation) => conversation.id === activeConversationId,
      ) ?? null,
    [activeConversationId, conversations],
  );

  function startNewConversation() {
    const id = createId();
    setConversations((current) => [
      ...current,
      { id, title: "Nouvelle conversation", messages: [] },
    ]);
    setActiveConversationId(id);
    setFeedbackNotice(null);
    setSelectedSource(null);
    setIsSourcePanelOpen(false);
  }

  function showSource(reference: ChatReference) {
    setSelectedSource(reference);
    setIsSourcePanelOpen(true);
  }

  async function handleSend(question: string) {
    if (isSendingRef.current) return;
    isSendingRef.current = true;

    const conversationId = activeConversationId ?? createId();
    const questionId = createId();
    const answerId = createId();
    const userMessage: ChatMessageData = {
      id: questionId,
      role: "user",
      content: question,
    };
    const answerMessage: ChatMessageData = {
      id: answerId,
      role: "assistant",
      content: "",
      references: [],
    };

    setActiveConversationId(conversationId);
    setConversations((current) => {
      const exists = current.some(
        (conversation) => conversation.id === conversationId,
      );
      if (!exists) {
        return [
          ...current,
          {
            id: conversationId,
            title: question,
            messages: [userMessage, answerMessage],
          },
        ];
      }

      return current.map((conversation) =>
        conversation.id !== conversationId
          ? conversation
          : {
              ...conversation,
              title:
                conversation.messages.length === 0 &&
                conversation.title === "Nouvelle conversation"
                  ? question
                  : conversation.title,
              messages: [
                ...conversation.messages,
                userMessage,
                answerMessage,
              ],
            },
      );
    });

    setIsSending(true);
    setFeedbackNotice(null);
    try {
      const response = await sendMessage(
        { question, role, conversation_id: conversationId },
        (event: ChatStreamEvent) => {
          if (event.type === "token") {
            setConversations((current) =>
              updateMessage(current, conversationId, answerId, (message) => ({
                ...message,
                content: message.content + event.token,
              })),
            );
          } else if (event.type === "sources") {
            setConversations((current) =>
              updateMessage(current, conversationId, answerId, (message) => ({
                ...message,
                references: event.references,
              })),
            );
          }
        },
      );

      setConversations((current) =>
        updateMessage(current, conversationId, answerId, (message) => ({
          ...message,
          content: response.answer,
          references: response.references,
          response,
        })),
      );
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? `La réponse n’a pas pu être obtenue : ${error.message}`
          : "La réponse n’a pas pu être obtenue en raison d’une erreur inattendue.";
      setConversations((current) =>
        updateMessage(current, conversationId, answerId, (message) => ({
          ...message,
          content: errorMessage,
          error: true,
        })),
      );
    } finally {
      isSendingRef.current = false;
      setIsSending(false);
    }
  }

  async function handleFeedback(
    requestId: string,
    rating: "up" | "down",
  ) {
    setFeedbackNotice(null);
    try {
      await sendFeedback({ request_id: requestId, rating });
      setFeedbackNotice("Merci, votre retour a bien été envoyé.");
    } catch (error) {
      setFeedbackNotice(
        error instanceof Error
          ? `Le retour n’a pas pu être envoyé : ${error.message}`
          : "Le retour n’a pas pu être envoyé en raison d’une erreur inattendue.",
      );
    }
  }

  const conversationSummaries = conversations.map(({ id, title }) => ({
    id,
    title: title.trim() || "Nouvelle conversation",
  }));

  return (
    <div className="flex h-dvh min-h-[32rem] overflow-hidden bg-white text-navy-900">
      <Sidebar
        conversations={conversationSummaries}
        activeConversationId={activeConversationId}
        role={role}
        displayName={displayName}
        onDisplayNameChange={setDisplayName}
        onRoleChange={setRole}
        onNewConversation={startNewConversation}
        onSelectConversation={setActiveConversationId}
      />

      <ChatArea
        messages={activeConversation?.messages ?? []}
        isSending={isSending}
        sourcesOpen={isSourcePanelOpen}
        role={role}
        displayName={displayName}
        onDisplayNameChange={setDisplayName}
        feedbackNotice={feedbackNotice}
        onSend={handleSend}
        onCitation={showSource}
        onToggleSources={() => setIsSourcePanelOpen((open) => !open)}
        onFeedback={handleFeedback}
      />

      <SourcePanel
        source={selectedSource}
        open={isSourcePanelOpen}
        onOpenChange={setIsSourcePanelOpen}
      />
    </div>
  );
}
