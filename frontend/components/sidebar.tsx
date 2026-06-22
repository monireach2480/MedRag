"use client"

import {
  MessageSquarePlus,
  MessagesSquare,
  Shield,
  Trash2,
  User as UserIcon,
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"

import { useAuth } from "@/components/auth-provider"
import { BrandLockup } from "@/components/brand"
import { useConversations } from "@/components/conversations-provider"
import { ThemeToggle } from "@/components/theme-toggle"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

function initials(name: string) {
  return (
    name
      .split(" ")
      .map((p) => p[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase() || "U"
  )
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const {
    conversations,
    loading,
    activeId,
    selectConversation,
    startNewConversation,
    removeConversation,
  } = useConversations()

  const [pendingDelete, setPendingDelete] = useState<string | null>(null)

  const navLinks = [
    { href: "/chat", label: "Chat", icon: MessagesSquare },
    { href: "/profile", label: "Profile", icon: UserIcon },
    ...(user?.is_admin
      ? [{ href: "/admin", label: "Admin", icon: Shield }]
      : []),
  ]

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex items-center justify-between px-4 py-4">
        <BrandLockup />
        <ThemeToggle />
      </div>

      <div className="px-3">
        <Button
          className="w-full justify-start"
          onClick={() => {
            startNewConversation()
            onNavigate?.()
          }}
        >
          <MessageSquarePlus data-icon="inline-start" />
          New chat
        </Button>
      </div>

      <div className="px-4 pb-2 pt-5">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Conversations
        </p>
      </div>

      <ScrollArea className="flex-1 px-3">
        <div className="flex flex-col gap-1 pb-4">
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))
          ) : conversations.length === 0 ? (
            <p className="px-2 py-6 text-sm text-muted-foreground">
              No conversations yet. Start a new chat to begin.
            </p>
          ) : (
            conversations.map((conv) => {
              const isActive = activeId === conv.id && pathname === "/chat"
              return (
                <div
                  key={conv.id}
                  className={cn(
                    "group flex items-center gap-1 rounded-md transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "hover:bg-sidebar-accent/60",
                  )}
                >
                  <button
                    type="button"
                    onClick={() => {
                      selectConversation(conv.id)
                      onNavigate?.()
                    }}
                    className="flex-1 truncate px-3 py-2 text-left text-sm"
                    title={conv.title}
                  >
                    {conv.title}
                  </button>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete ${conv.title}`}
                    className="mr-1 size-7 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                    onClick={() => setPendingDelete(conv.id)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              )
            })
          )}
        </div>
      </ScrollArea>

      <Separator />

      <nav className="flex flex-col gap-1 p-3">
        {navLinks.map((link) => {
          const Icon = link.icon
          const isActive =
            pathname === link.href || pathname.startsWith(`${link.href}/`)
          return (
            <Link
              key={link.href}
              href={link.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60",
              )}
            >
              <Icon className="size-4" />
              {link.label}
            </Link>
          )
        })}
      </nav>

      <Separator />

      <div className="flex items-center gap-3 p-3">
        <Avatar className="size-9">
          <AvatarFallback className="bg-primary/10 text-sm text-primary">
            {user ? initials(user.full_name) : "U"}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{user?.full_name}</p>
          <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            void logout()
            onNavigate?.()
          }}
        >
          Logout
        </Button>
      </div>

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes the conversation and its messages. This
              action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingDelete) void removeConversation(pendingDelete)
                setPendingDelete(null)
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
