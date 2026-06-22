"use client"

import { ArrowUp, MessagesSquare, Square, Trash2 } from "lucide-react"
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react"
import { toast } from "sonner"

import { useConversations } from "@/components/conversations-provider"
import { MessageBubble } from "@/components/message-bubble"
import { Button } from "@/components/ui/button"
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiError } from "@/lib/api"
import {
  getConversationMessages,
  saveConversationMessage,
  streamChat,
} from "@/lib/auth"
import type { ChatMessage, Source, StreamEvent } from "@/lib/types"

const SUGGESTIONS = [
  "What are the first-line treatments for type 2 diabetes?",
  "Summarize the contraindications for NSAIDs.",
  "What is the recommended dosage of amoxicillin for adults?",
]

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function ChatWindow() {
  const {
    activeId,
    createConversation,
    prependConversation,
    setActiveId,
  } = useConversations()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [streaming, setStreaming] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)

  const abortRef = useRef<AbortController | null>(null)
  const scrollEndRef = useRef<HTMLDivElement | null>(null)
  // Tracks the conversation id messages are currently being saved against,
  // so streaming started before a conversation existed still persists.
  const activeIdRef = useRef<string | null>(activeId)

  useEffect(() => {
    activeIdRef.current = activeId
  }, [activeId])

  // Load (or clear) messages whenever the active conversation changes.
  useEffect(() => {
    let cancelled = false

    async function load() {
      if (!activeId) {
        setMessages([])
        return
      }
      setLoadingHistory(true)
      try {
        const history = await getConversationMessages(activeId)
        if (cancelled) return
        setMessages(
          history.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            sources: (m.sources as Source[] | undefined) ?? undefined,
          })),
        )
      } catch {
        if (!cancelled) setMessages([])
      } finally {
        if (!cancelled) setLoadingHistory(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [activeId])

  // Auto-scroll to the newest message.
  useEffect(() => {
    scrollEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const updateAssistant = useCallback(
    (assistantId: string, updater: (prev: ChatMessage) => ChatMessage) => {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? updater(m) : m)),
      )
    },
    [],
  )

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || streaming) return

      setInput("")

      const userMessage: ChatMessage = { id: uid(), role: "user", content: trimmed }
      const assistantId = uid()
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        streaming: true,
      }
      setMessages((prev) => [...prev, userMessage, assistantMessage])

      setStreaming(true)
      const controller = new AbortController()
      abortRef.current = controller

      let answer = ""
      let finalSources: Source[] | undefined

      const onEvent = (event: StreamEvent) => {
        switch (event.type) {
          case "conversation_id": {
            const newId = String(event.conversation_id)
            activeIdRef.current = newId
            setActiveId(newId)
            prependConversation({
              id: newId,
              title: trimmed.length > 40 ? trimmed.slice(0, 40) + "..." : trimmed,
              created_at: new Date().toISOString(),
            })
            break
          }
          case "chunk":
            answer += event.content
            updateAssistant(assistantId, (m) => ({ ...m, content: answer }))
            break
          case "sources":
            finalSources = event.sources
            updateAssistant(assistantId, (m) => ({
              ...m,
              sources: event.sources,
              disclaimer: event.disclaimer,
            }))
            break
          case "done":
            updateAssistant(assistantId, (m) => ({ ...m, streaming: false }))
            break
          case "error":
            toast.error(event.detail || "Something went wrong")
            updateAssistant(assistantId, (m) => ({
              ...m,
              streaming: false,
              content: m.content || "Sorry, I ran into an error answering that.",
            }))
            break
        }
      }

      try {
        await streamChat(
          { message: trimmed, conversation_id: activeIdRef.current ?? undefined },
          onEvent,
          controller.signal,
        )
      } catch (err) {
        const message =
          err instanceof ApiError ? err.detail : "Streaming failed. Try again."
        if (!controller.signal.aborted) toast.error(message)
        updateAssistant(assistantId, (m) => ({
          ...m,
          streaming: false,
          content: m.content || "Sorry, I couldn't complete that response.",
        }))
      } finally {
        updateAssistant(assistantId, (m) => ({ ...m, streaming: false }))
        setStreaming(false)
        abortRef.current = null
        // ← no saveConversationMessage here, backend handles it
      }
    },
    [streaming, updateAssistant, setActiveId, prependConversation],
  )

  function stop() {
    abortRef.current?.abort()
    setStreaming(false)
  }

  function clearChat() {
    if (streaming) stop()
    setMessages([])
    setActiveId(null)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void send(input)
    }
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div className="min-w-0">
          <h1 className="truncate text-base font-semibold">Medical Assistant</h1>
          <p className="text-xs text-muted-foreground">
            Answers grounded in your clinical document library
          </p>
        </div>
        {hasMessages && (
          <Button variant="outline" size="sm" onClick={clearChat}>
            <Trash2 data-icon="inline-start" />
            Clear
          </Button>
        )}
      </header>

      <ScrollArea className="min-h-0 flex-1">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
          {loadingHistory ? (
            <div className="flex flex-col gap-6">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <Skeleton className="h-16 w-2/3" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ))}
            </div>
          ) : !hasMessages ? (
            <Empty className="py-10">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <MessagesSquare />
                </EmptyMedia>
                <EmptyTitle>Ask a medical question</EmptyTitle>
                <EmptyDescription>
                  Responses are generated from your ingested documents and
                  include source citations. This tool does not replace
                  professional medical advice.
                </EmptyDescription>
              </EmptyHeader>
              <div className="mt-2 flex flex-col gap-2">
                {SUGGESTIONS.map((s) => (
                  <Button
                    key={s}
                    variant="outline"
                    className="h-auto whitespace-normal py-2 text-left"
                    onClick={() => void send(s)}
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </Empty>
          ) : (
            <div className="flex flex-col gap-6">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
            </div>
          )}
          <div ref={scrollEndRef} />
        </div>
      </ScrollArea>

      <div className="border-t bg-background px-4 py-4 sm:px-6">
        <div className="mx-auto w-full max-w-3xl">
          <InputGroup>
            <InputGroupTextarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about symptoms, treatments, dosages..."
              rows={1}
              className="max-h-40 min-h-10"
              aria-label="Message"
            />
            <InputGroupAddon align="block-end">
              <span className="text-xs text-muted-foreground">
                Enter to send, Shift+Enter for a new line
              </span>
              {streaming ? (
                <InputGroupButton
                  size="icon-sm"
                  variant="outline"
                  className="ml-auto"
                  aria-label="Stop generating"
                  onClick={stop}
                >
                  <Square />
                </InputGroupButton>
              ) : (
                <InputGroupButton
                  size="icon-sm"
                  variant="default"
                  className="ml-auto"
                  aria-label="Send message"
                  disabled={!input.trim()}
                  onClick={() => void send(input)}
                >
                  <ArrowUp />
                </InputGroupButton>
              )}
            </InputGroupAddon>
          </InputGroup>
        </div>
      </div>
    </div>
  )
}
