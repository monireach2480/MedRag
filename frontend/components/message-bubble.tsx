"use client"

import { Check, Copy, Stethoscope, TriangleAlert } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { SourceList } from "@/components/source-card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import type { ChatMessage } from "@/lib/types"
import { cn } from "@/lib/utils"

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-1" aria-label="Assistant is typing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="size-2 animate-bounce rounded-full bg-muted-foreground/60"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </span>
  )
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === "user"

  async function copy() {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      toast.success("Answer copied")
      setTimeout(() => setCopied(false), 1500)
    } catch {
      toast.error("Could not copy to clipboard")
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end gap-3">
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground">
          {message.content}
        </div>
      </div>
    )
  }

  const showTyping = message.streaming && !message.content

  return (
    <div className="flex gap-3">
      <Avatar className="size-8 shrink-0">
        <AvatarFallback className="bg-primary/10 text-primary">
          <Stethoscope className="size-4" />
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "group rounded-2xl rounded-tl-sm border bg-card px-4 py-3 text-sm leading-relaxed",
          )}
        >
          {showTyping ? (
            <TypingDots />
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              {message.streaming && (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-foreground align-middle" />
              )}
            </div>
          )}

          {!message.streaming && message.content && (
            <div className="mt-2 flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-muted-foreground"
                onClick={copy}
              >
                {copied ? (
                  <Check data-icon="inline-start" />
                ) : (
                  <Copy data-icon="inline-start" />
                )}
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>
          )}
        </div>

        {message.sources && message.sources.length > 0 && (
          <SourceList sources={message.sources} />
        )}

        {message.disclaimer && (
          <Alert className="mt-3 border-amber-500/30 bg-amber-500/10 text-amber-900 dark:text-amber-200">
            <TriangleAlert className="size-4" />
            <AlertDescription className="text-amber-900 dark:text-amber-200">
              {message.disclaimer}
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  )
}
