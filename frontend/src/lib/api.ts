import type {
  ChatReference,
  ChatRequest,
  ChatResponse,
  ChatStreamEvent,
  ChatStreamListener,
  FeedbackRequest,
  RefusalReason,
} from "@/lib/types";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

const mockReferences: ChatReference[] = [
  {
    n: 1,
    doc_id: "DEMO-GUIDE-001",
    title: "Guide fictif des opérations courantes",
    version: "1.2",
    page: 4,
    access_level: "public",
    excerpt:
      "Pour une demande courante, l’agent vérifie l’identité du demandeur et consulte les pièces justificatives prévues par la procédure de démonstration.",
  },
  {
    n: 2,
    doc_id: "DEMO-PROC-002",
    title: "Procédure fictive de traitement des demandes",
    version: "2.0",
    page: 7,
    access_level: "public",
    excerpt:
      "La demande est enregistrée dans le suivi fictif. Le délai indicatif de traitement est communiqué au client après vérification du dossier.",
  },
];

const demoAnswer =
  "Pour une demande courante, vérifiez l’identité du demandeur et les pièces justificatives prévues [1]. Enregistrez ensuite la demande dans le suivi et communiquez le délai indicatif après vérification du dossier [2].";

const refusalAnswer =
  "Je ne peux pas répondre de façon fiable : les documents fictifs disponibles ne contiennent pas assez d’informations sur ce point. Vous pouvez préciser votre demande ou consulter la procédure applicable.";

const accessDeniedAnswer =
  "L’accès à cette information est réservé au rôle Conformité dans cette démonstration. Aucune source protégée n’a été transmise.";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseReference(value: unknown): ChatReference {
  if (!isRecord(value)) {
    throw new Error("Une référence reçue du serveur est invalide.");
  }

  const accessLevel = value.access_level;
  if (
    typeof value.n !== "number" ||
    typeof value.doc_id !== "string" ||
    typeof value.title !== "string" ||
    typeof value.version !== "string" ||
    typeof value.page !== "number" ||
    (accessLevel !== "public" && accessLevel !== "conformite") ||
    typeof value.excerpt !== "string"
  ) {
    throw new Error("Une référence reçue du serveur ne respecte pas le contrat.");
  }

  return {
    n: value.n,
    doc_id: value.doc_id,
    title: value.title,
    version: value.version,
    page: value.page,
    access_level: accessLevel,
    excerpt: value.excerpt,
  };
}

function parseReferences(value: unknown): ChatReference[] {
  if (!Array.isArray(value)) {
    throw new Error("La liste des références reçue du serveur est invalide.");
  }
  return value.map(parseReference);
}

function parseReason(value: unknown): RefusalReason | null {
  if (value === null) return null;
  switch (value) {
    case "retrieval_insuffisant":
      return "retrieval_insuffisant";
    case "refus_modele":
      return "refus_modele";
    case "acces_refuse":
      return "acces_refuse";
    case "erreur":
      return "erreur";
    default:
      break;
  }
  throw new Error("Le motif de refus reçu du serveur est invalide.");
}

function parseChatResponse(value: unknown): ChatResponse {
  if (
    !isRecord(value) ||
    typeof value.request_id !== "string" ||
    typeof value.answer !== "string" ||
    typeof value.refused !== "boolean" ||
    typeof value.latency_ms !== "number" ||
    !Number.isFinite(value.latency_ms)
  ) {
    throw new Error("La réponse reçue du serveur ne respecte pas le contrat.");
  }

  return {
    request_id: value.request_id,
    answer: value.answer,
    refused: value.refused,
    reason: parseReason(value.reason),
    references: parseReferences(value.references),
    latency_ms: value.latency_ms,
  };
}

function createRequestId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return `demo-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function createMockResponse(
  request: ChatRequest,
  latency_ms: number,
): ChatResponse {
  const question = request.question.toLocaleLowerCase("fr");
  const restrictedTopic =
    /\b(kyc|conformité|confidentiel|interne|soupçon)\b/i.test(question);
  const refusalRequested =
    /\b(refus|information insuffisante|hors corpus|sans document)\b/i.test(
      question,
    );

  if (request.role === "agent" && restrictedTopic) {
    return {
      request_id: createRequestId(),
      answer: accessDeniedAnswer,
      refused: true,
      reason: "acces_refuse",
      references: [],
      latency_ms,
    };
  }

  if (refusalRequested) {
    return {
      request_id: createRequestId(),
      answer: refusalAnswer,
      refused: true,
      reason: "retrieval_insuffisant",
      references: [],
      latency_ms,
    };
  }

  return {
    request_id: createRequestId(),
    answer: demoAnswer,
    refused: false,
    reason: null,
    references: mockReferences.map((reference) => ({ ...reference })),
    latency_ms,
  };
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function sendMockMessage(
  request: ChatRequest,
  onEvent?: ChatStreamListener,
): Promise<ChatResponse> {
  const startedAt = Date.now();
  const response = createMockResponse(request, 0);
  const words = response.answer.match(/\S+\s*/g) ?? [];
  let streamedAnswer = "";

  for (const token of words) {
    streamedAnswer += token;
    onEvent?.({ type: "token", token });
    await wait(35);
  }

  response.answer = streamedAnswer;
  response.latency_ms = Date.now() - startedAt;
  onEvent?.({ type: "sources", references: response.references });
  onEvent?.({ type: "done", response });
  return response;
}

function getErrorMessage(body: unknown, fallback: string): string {
  if (isRecord(body) && typeof body.detail === "string") {
    return body.detail;
  }
  if (isRecord(body) && typeof body.message === "string") {
    return body.message;
  }
  return fallback;
}

async function readSseResponse(
  body: ReadableStream<Uint8Array>,
  onEvent?: ChatStreamListener,
): Promise<ChatResponse> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";
  let dataLines: string[] = [];
  let streamedAnswer = "";
  let references: ChatReference[] = [];
  let finalResponse: ChatResponse | undefined;

  const dispatch = (): void => {
    if (dataLines.length === 0) {
      eventName = "message";
      return;
    }

    const rawData = dataLines.join("\n");
    let payload: unknown;
    try {
      payload = JSON.parse(rawData);
    } catch {
      throw new Error(`L’événement SSE "${eventName}" contient un JSON invalide.`);
    }

    if (eventName === "token") {
      const token =
        typeof payload === "string"
          ? payload
          : isRecord(payload) && typeof payload.token === "string"
            ? payload.token
            : undefined;
      if (token === undefined) {
        throw new Error("L’événement SSE « token » est invalide.");
      }
      streamedAnswer += token;
      onEvent?.({ type: "token", token });
    } else if (eventName === "sources") {
      const value = Array.isArray(payload)
        ? payload
        : isRecord(payload)
          ? payload.references
          : undefined;
      references = parseReferences(value);
      onEvent?.({ type: "sources", references });
    } else if (eventName === "done") {
      const value =
        isRecord(payload) && isRecord(payload.response)
          ? payload.response
          : payload;
      if (!isRecord(value)) {
        throw new Error("L’événement SSE « done » est invalide.");
      }
      finalResponse = parseChatResponse({
        ...value,
        answer:
          typeof value.answer === "string" ? value.answer : streamedAnswer,
        references: Array.isArray(value.references)
          ? value.references
          : references,
      });
      onEvent?.({ type: "done", response: finalResponse });
    }

    eventName = "message";
    dataLines = [];
  };

  const processLine = (line: string): void => {
    if (line === "") {
      dispatch();
      return;
    }
    if (line.startsWith(":")) return;

    const separator = line.indexOf(":");
    const field = separator === -1 ? line : line.slice(0, separator);
    const value = separator === -1 ? "" : line.slice(separator + 1).replace(/^ /, "");
    if (field === "event") eventName = value;
    if (field === "data") dataLines.push(value);
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const line of lines) processLine(line);
    }

    buffer += decoder.decode();
    if (buffer.length > 0) processLine(buffer);
    dispatch();
  } finally {
    reader.releaseLock();
  }

  if (!finalResponse) {
    throw new Error("Le flux SSE s’est terminé sans événement « done ».");
  }
  return finalResponse;
}

export async function sendMessage(
  request: ChatRequest,
  onEvent?: ChatStreamListener,
): Promise<ChatResponse> {
  if (USE_MOCK) {
    return sendMockMessage(request, onEvent);
  }

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      Accept: "text/event-stream, application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let details: unknown;
    try {
      details = await response.json();
    } catch {
      details = undefined;
    }
    throw new Error(
      getErrorMessage(
        details,
        `La requête a échoué (HTTP ${response.status}).`,
      ),
    );
  }

  if (response.headers.get("content-type")?.includes("text/event-stream")) {
    if (!response.body) {
      throw new Error("Le serveur a ouvert un flux SSE sans corps de réponse.");
    }
    return readSseResponse(response.body, onEvent);
  }

  const result = parseChatResponse(await response.json());
  onEvent?.({ type: "token", token: result.answer });
  onEvent?.({ type: "sources", references: result.references });
  onEvent?.({ type: "done", response: result });
  return result;
}

export async function sendFeedback(
  feedback: FeedbackRequest,
): Promise<void> {
  if (USE_MOCK) return;

  const response = await fetch(`${API_BASE_URL}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedback),
  });

  if (!response.ok) {
    let details: unknown;
    try {
      details = await response.json();
    } catch {
      details = undefined;
    }
    throw new Error(
      getErrorMessage(
        details,
        `L’envoi du retour a échoué (HTTP ${response.status}).`,
      ),
    );
  }
}
