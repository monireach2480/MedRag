import type { ReactNode } from "react"

import { AuthProvider } from "@/components/auth-provider"
import { BrandLockup } from "@/components/brand"
import { ThemeToggle } from "@/components/theme-toggle"

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <div className="flex min-h-svh flex-col bg-muted/30">
        <header className="flex items-center justify-between px-6 py-5">
          <BrandLockup />
          <ThemeToggle />
        </header>
        <main className="flex flex-1 items-center justify-center px-4 pb-16">
          <div className="w-full max-w-md">{children}</div>
        </main>
      </div>
    </AuthProvider>
  )
}
