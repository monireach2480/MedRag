"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

import { AdminView } from "@/components/admin-view"
import { useAuth } from "@/components/auth-provider"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"

export default function AdminPage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  // Redirect any non-admin user away from the admin panel.
  useEffect(() => {
    if (!loading && user && !user.is_admin) {
      router.replace("/chat")
    }
  }, [loading, user, router])

  if (loading || !user || !user.is_admin) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
        <Skeleton className="mb-6 h-8 w-48" />
        <Skeleton className="mb-8 h-48 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <AdminView />
    </ScrollArea>
  )
}
