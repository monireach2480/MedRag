"use client"

import { FileText, Loader2, Trash2 } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"

import { UploadDropzone } from "@/components/upload-dropzone"
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
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiError } from "@/lib/api"
import { deleteDocument, listDocuments } from "@/lib/auth"
import type { IngestedDocument } from "@/lib/types"

export function AdminView() {
  const [documents, setDocuments] = useState<IngestedDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.detail : "Could not load documents",
      )
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function confirmDelete() {
    if (!pendingDelete) return
    setDeleting(true)
    try {
      await deleteDocument(pendingDelete)
      toast.success("Document deleted")
      setDocuments((prev) => prev.filter((d) => d.filename !== pendingDelete))
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "Delete failed")
    } finally {
      setDeleting(false)
      setPendingDelete(null)
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          Document Library
        </h1>
        <p className="text-sm text-muted-foreground">
          Upload and manage the PDFs that power the assistant&apos;s answers.
        </p>
      </div>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Upload a document</CardTitle>
          <CardDescription>
            PDFs are split into chunks and embedded into the vector store.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UploadDropzone onUploaded={load} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ingested documents</CardTitle>
          <CardDescription>
            {documents.length > 0
              ? `${documents.length} document${documents.length === 1 ? "" : "s"} in the knowledge base.`
              : "Documents you upload will appear here."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex flex-col gap-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full rounded-lg" />
              ))}
            </div>
          ) : documents.length === 0 ? (
            <Empty className="py-8">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <FileText />
                </EmptyMedia>
                <EmptyTitle>No documents yet</EmptyTitle>
                <EmptyDescription>
                  Upload your first PDF to start building the knowledge base.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : (
            <div className="flex flex-col gap-2">
              {documents.map((doc) => (
                <div
                  key={doc.filename}
                  className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2.5"
                >
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <FileText className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {doc.chunks} chunk{doc.chunks === 1 ? "" : "s"}
                    </p>
                  </div>
                  <Badge variant="secondary" className="shrink-0">
                    {doc.chunks}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Delete ${doc.filename}`}
                    className="shrink-0 text-muted-foreground"
                    onClick={() => setPendingDelete(doc.filename)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && !deleting && setPendingDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete document?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes all vector store entries for{" "}
              <span className="font-medium text-foreground">{pendingDelete}</span>
              . The assistant will no longer cite this document.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault()
                void confirmDelete()
              }}
              disabled={deleting}
            >
              {deleting && (
                <Loader2 data-icon="inline-start" className="animate-spin" />
              )}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
