"use client"

import { FileUp, Loader2, UploadCloud } from "lucide-react"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { uploadDocument } from "@/lib/auth"
import { cn } from "@/lib/utils"

export function UploadDropzone({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [fileName, setFileName] = useState<string | null>(null)

  async function handleFile(file: File) {
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Only PDF files are supported")
      return
    }

    setUploading(true)
    setProgress(0)
    setFileName(file.name)

    try {
      const result = await uploadDocument(file, setProgress)
      toast.success(
        `Ingested ${result.filename} (${result.chunks_inserted} chunks)`,
      )
      onUploaded()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed")
    } finally {
      setUploading(false)
      setProgress(0)
      setFileName(null)
      if (inputRef.current) inputRef.current.value = ""
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload a PDF document"
      onClick={() => !uploading && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !uploading) {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        if (!uploading) setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        if (uploading) return
        const file = e.dataTransfer.files?.[0]
        if (file) void handleFile(file)
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
        dragging
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/50 hover:bg-muted/40",
        uploading && "pointer-events-none opacity-90",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) void handleFile(file)
        }}
      />

      {uploading ? (
        <>
          <Loader2 className="size-8 animate-spin text-primary" />
          <div className="w-full max-w-xs">
            <p className="mb-2 truncate text-sm font-medium">{fileName}</p>
            <Progress value={progress} />
            <p className="mt-1 text-xs text-muted-foreground">
              {progress}% uploaded
            </p>
          </div>
        </>
      ) : (
        <>
          <span className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <UploadCloud className="size-6" />
          </span>
          <div>
            <p className="text-sm font-medium">
              Drag &amp; drop a PDF here, or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              The document will be chunked and ingested into the knowledge base.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              inputRef.current?.click()
            }}
          >
            <FileUp data-icon="inline-start" />
            Choose file
          </Button>
        </>
      )}
    </div>
  )
}
