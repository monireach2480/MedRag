import { Stethoscope } from "lucide-react"

import { cn } from "@/lib/utils"

export function BrandMark({
  className,
  iconClassName,
}: {
  className?: string
  iconClassName?: string
}) {
  return (
    <span
      className={cn(
        "flex items-center justify-center rounded-xl bg-primary text-primary-foreground",
        className,
      )}
    >
      <Stethoscope className={cn("size-5", iconClassName)} aria-hidden="true" />
    </span>
  )
}

export function BrandLockup({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <BrandMark className="size-9" />
      <div className="flex flex-col leading-none">
        <span className="text-base font-semibold tracking-tight">MedRAG</span>
        <span className="text-xs text-muted-foreground">Clinical Assistant</span>
      </div>
    </div>
  )
}
