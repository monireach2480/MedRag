import { FileText } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Source } from "@/lib/types"

export function SourceCard({ source }: { source: Source }) {
  return (
    <Card className="gap-0 bg-muted/40 py-3">
      <CardHeader className="px-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <FileText className="size-4 shrink-0 text-primary" />
          <span className="truncate" title={source.filename}>
            {source.filename}
          </span>
          <Badge variant="secondary" className="ml-auto shrink-0">
            p. {source.page}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="px-3 pt-2">
        <p className="line-clamp-4 text-xs leading-relaxed text-muted-foreground">
          {source.excerpt}
        </p>
      </CardContent>
    </Card>
  )
}

export function SourceList({ sources }: { sources: Source[] }) {
  if (!sources.length) return null
  return (
    <div className="mt-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sources
      </p>
      <div className="grid gap-2 sm:grid-cols-2">
        {sources.map((source, i) => (
          <SourceCard key={`${source.filename}-${source.page}-${i}`} source={source} />
        ))}
      </div>
    </div>
  )
}
