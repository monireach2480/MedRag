import type { ReactNode } from "react"

import { AppShell } from "@/components/app-shell"
import { AuthProvider } from "@/components/auth-provider"
import { ConversationsProvider } from "@/components/conversations-provider"

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <ConversationsProvider>
        <AppShell>{children}</AppShell>
      </ConversationsProvider>
    </AuthProvider>
  )
}
