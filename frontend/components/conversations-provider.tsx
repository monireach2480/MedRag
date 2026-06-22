"use client"

import { usePathname, useRouter } from "next/navigation"
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { toast } from "sonner"

import {
  createConversation as createConversationRequest,
  deleteConversation as deleteConversationRequest,
  listConversations,
} from "@/lib/auth"
import type { Conversation } from "@/lib/types"

interface ConversationsContextValue {
  conversations: Conversation[]
  loading: boolean
  activeId: string | null
  setActiveId: (id: string | null) => void
  selectConversation: (id: string) => void
  startNewConversation: () => void
  createConversation: (title: string) => Promise<Conversation>
  removeConversation: (id: string) => Promise<void>
  prependConversation: (conversation: Conversation) => void
  refresh: () => Promise<void>
}

const ConversationsContext = createContext<ConversationsContextValue | null>(null)

export function ConversationsProvider({ children }: { children: ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [activeId, setActiveId] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const list = await listConversations()
      setConversations(list)
    } catch {
      // A fresh user may have none; treat errors as empty silently.
      setConversations([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const selectConversation = useCallback(
    (id: string) => {
      setActiveId(id)
      if (pathname !== "/chat") {
        router.push("/chat")
      }
    },
    [pathname, router],
  )

  const startNewConversation = useCallback(() => {
    setActiveId(null)
    if (pathname !== "/chat") {
      router.push("/chat")
    }
  }, [pathname, router])

  const createConversation = useCallback(async (title: string) => {
    const created = await createConversationRequest(title)
    setConversations((prev) => [created, ...prev])
    setActiveId(created.id)
    return created
  }, [])

  const prependConversation = useCallback((conversation: Conversation) => {
    setConversations((prev) => {
      if (prev.some((c) => c.id === conversation.id)) return prev
      return [conversation, ...prev]
    })
  }, [])

  const removeConversation = useCallback(
    async (id: string) => {
      try {
        await deleteConversationRequest(id)
        setConversations((prev) => prev.filter((c) => c.id !== id))
        setActiveId((current) => (current === id ? null : current))
        toast.success("Conversation deleted")
      } catch {
        toast.error("Could not delete the conversation")
      }
    },
    [],
  )

  const value = useMemo(
    () => ({
      conversations,
      loading,
      activeId,
      setActiveId,
      selectConversation,
      startNewConversation,
      createConversation,
      removeConversation,
      prependConversation,
      refresh,
    }),
    [
      conversations,
      loading,
      activeId,
      selectConversation,
      startNewConversation,
      createConversation,
      removeConversation,
      prependConversation,
      refresh,
    ],
  )

  return (
    <ConversationsContext.Provider value={value}>
      {children}
    </ConversationsContext.Provider>
  )
}

export function useConversations() {
  const ctx = useContext(ConversationsContext)
  if (!ctx) {
    throw new Error("useConversations must be used within a ConversationsProvider")
  }
  return ctx
}
