"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2 } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { useAuth } from "@/components/auth-provider"
import { PasswordInput } from "@/components/password-input"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ApiError } from "@/lib/api"
import { updatePassword, updateProfile } from "@/lib/auth"

const profileSchema = z.object({
  full_name: z.string().min(2, "Please enter your full name"),
})

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })

type ProfileValues = z.infer<typeof profileSchema>
type PasswordValues = z.infer<typeof passwordSchema>

function ProfileForm() {
  const { user, setUser } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: { full_name: user?.full_name ?? "" },
  })

  async function onSubmit(values: ProfileValues) {
    try {
      const updated = await updateProfile(values.full_name)
      setUser(updated)
      toast.success("Profile updated")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "Update failed")
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile details</CardTitle>
        <CardDescription>Update your account information.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="email">Email</FieldLabel>
              <Input id="email" value={user?.email ?? ""} readOnly disabled />
              <FieldDescription>Your email cannot be changed.</FieldDescription>
            </Field>
            <Field data-invalid={!!errors.full_name}>
              <FieldLabel htmlFor="full_name">Full name</FieldLabel>
              <Input
                id="full_name"
                aria-invalid={!!errors.full_name}
                {...register("full_name")}
              />
              <FieldError
                errors={errors.full_name ? [errors.full_name] : undefined}
              />
            </Field>
          </FieldGroup>
        </CardContent>
        <CardFooter className="mt-6">
          <Button type="submit" disabled={isSubmitting || !isDirty}>
            {isSubmitting && (
              <Loader2 data-icon="inline-start" className="animate-spin" />
            )}
            Save changes
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}

function PasswordForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  })

  async function onSubmit(values: PasswordValues) {
    try {
      await updatePassword(values.current_password, values.new_password)
      toast.success("Password updated")
      reset()
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.detail : "Could not update password",
      )
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Change password</CardTitle>
        <CardDescription>
          Use a strong password you don&apos;t reuse elsewhere.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <CardContent>
          <FieldGroup>
            <Field data-invalid={!!errors.current_password}>
              <FieldLabel htmlFor="current_password">
                Current password
              </FieldLabel>
              <PasswordInput
                id="current_password"
                autoComplete="current-password"
                aria-invalid={!!errors.current_password}
                {...register("current_password")}
              />
              <FieldError
                errors={
                  errors.current_password ? [errors.current_password] : undefined
                }
              />
            </Field>
            <Field data-invalid={!!errors.new_password}>
              <FieldLabel htmlFor="new_password">New password</FieldLabel>
              <PasswordInput
                id="new_password"
                autoComplete="new-password"
                aria-invalid={!!errors.new_password}
                {...register("new_password")}
              />
              <FieldError
                errors={errors.new_password ? [errors.new_password] : undefined}
              />
            </Field>
            <Field data-invalid={!!errors.confirm_password}>
              <FieldLabel htmlFor="confirm_password">
                Confirm new password
              </FieldLabel>
              <PasswordInput
                id="confirm_password"
                autoComplete="new-password"
                aria-invalid={!!errors.confirm_password}
                {...register("confirm_password")}
              />
              <FieldError
                errors={
                  errors.confirm_password ? [errors.confirm_password] : undefined
                }
              />
            </Field>
          </FieldGroup>
        </CardContent>
        <CardFooter className="mt-6">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && (
              <Loader2 data-icon="inline-start" className="animate-spin" />
            )}
            Update password
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}

export function ProfileView() {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground">
          Manage your account settings and security.
        </p>
      </div>
      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
        </TabsList>
        <TabsContent value="details" className="mt-4">
          <ProfileForm />
        </TabsContent>
        <TabsContent value="password" className="mt-4">
          <PasswordForm />
        </TabsContent>
      </Tabs>
    </div>
  )
}
