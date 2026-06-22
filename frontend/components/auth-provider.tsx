"use client"

import { useRouter } from "next/navigation"
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  type LoginPayload,
  type RegisterPayload,
} from "@/lib/auth"
import type { User } from "@/lib/types"

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (payload: LoginPayload) => Promise<User>
  register: (payload: RegisterPayload) => Promise<User>
  logout: () => Promise<void>
  refresh: () => Promise<void>
  setUser: (user: User | null) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({
  children,
  initialUser = null,
}: {
  children: ReactNode
  initialUser?: User | null
}) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(initialUser)
  const [loading, setLoading] = useState(initialUser === null)

  const refresh = useCallback(async () => {
    try {
      const me = await getCurrentUser()
      setUser(me)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (initialUser === null) {
      void refresh()
    }
  }, [initialUser, refresh])

  const login = useCallback(async (payload: LoginPayload) => {
    const u = await loginRequest(payload)
    setUser(u)
    return u
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    // Create the account
    await registerRequest(payload)
    // Then login to get the JWT cookie set
    const u = await loginRequest({ email: payload.email, password: payload.password })
    setUser(u)
    return u
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
      router.replace("/login")
    }
  }, [router])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refresh, setUser }),
    [user, loading, login, register, logout, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return ctx
}
