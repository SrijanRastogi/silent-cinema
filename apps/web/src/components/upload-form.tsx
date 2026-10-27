import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { ApiError, uploadFilm } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBytes } from "@/lib/format";

const ACCEPTED = ".mp4,.mkv,.mov,.avi,.mpg,.mpeg,.webm,video/*";

export function UploadForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("eng");
  const [validation, setValidation] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: ({ selected, ocrLanguage }: { selected: File; ocrLanguage: string }) =>
      uploadFilm(selected, ocrLanguage),
    onSuccess: async (film) => {
      await queryClient.invalidateQueries({ queryKey: ["films"] });
      void navigate(`/films/${film.id}`);
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file === null) {
      setValidation("Choose a video file first.");
      return;
    }
    if (!/^[a-z0-9_]+(\+[a-z0-9_]+)*$/.test(language)) {
      setValidation("Use a Tesseract language tag such as eng, deu, or fra.");
      return;
    }
    setValidation(null);
    upload.mutate({ selected: file, ocrLanguage: language });
  }

  const error = upload.error;
  const errorMessage =
    error instanceof ApiError
      ? error.message
      : error
        ? "The upload could not be completed."
        : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Import a film</CardTitle>
        <CardDescription>
          The file is stored locally and analysed in one request: probe, intertitle detection, then
          OCR. Upload a short reel first. Long films can take several minutes, and no progress
          estimate is invented while the request is open.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="film-file" className="block text-sm font-medium">
              Film file
            </label>
            <input
              id="film-file"
              name="file"
              type="file"
              accept={ACCEPTED}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setValidation(null);
              }}
              disabled={upload.isPending}
              className="block w-full cursor-pointer rounded-md border border-input bg-background px-3 py-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-secondary file:px-3 file:py-1.5 file:text-sm file:font-medium hover:file:bg-accent disabled:cursor-not-allowed disabled:opacity-60"
            />
            <p className="text-xs leading-5 text-muted-foreground">
              {file
                ? `${file.name} — ${formatBytes(file.size)}`
                : "MP4, MKV, MOV, AVI, MPG, MPEG, or WebM. Maximum 2 GiB in this build."}
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="ocr-language" className="block text-sm font-medium">
              Tesseract language
            </label>
            <input
              id="ocr-language"
              name="ocr_language"
              value={language}
              onChange={(event) => setLanguage(event.target.value.trim())}
              disabled={upload.isPending}
              spellCheck={false}
              autoComplete="off"
              aria-describedby="ocr-language-help"
              className="timecode h-10 w-full max-w-48 rounded-md border border-input bg-background px-3 text-sm disabled:opacity-60"
            />
            <p id="ocr-language-help" className="text-xs leading-5 text-muted-foreground">
              A language pack installed next to Tesseract on this machine. English is the only pack
              verified on the synthetic fixture.
            </p>
          </div>

          {validation ? (
            <p role="alert" className="text-sm text-danger">
              {validation}
            </p>
          ) : null}
          {errorMessage ? (
            <div role="alert" className="rounded-md border border-danger/40 bg-danger/5 px-3 py-2">
              <p className="text-sm font-medium text-danger">Upload failed</p>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{errorMessage}</p>
              {error instanceof ApiError && error.requestId ? (
                <p className="timecode mt-1 text-xs text-muted-foreground">
                  Request {error.requestId}
                </p>
              ) : null}
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={upload.isPending || file === null}>
              {upload.isPending ? (
                <Loader2 aria-hidden="true" className="size-4 animate-spin" />
              ) : (
                <Upload aria-hidden="true" className="size-4" />
              )}
              {upload.isPending ? "Detecting and reading titles…" : "Import and scan"}
            </Button>
            {upload.isPending ? (
              <p className="text-xs leading-5 text-muted-foreground" aria-live="polite">
                The request is open. Keep this tab open; the server is decoding frames and running
                OCR now.
              </p>
            ) : null}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
