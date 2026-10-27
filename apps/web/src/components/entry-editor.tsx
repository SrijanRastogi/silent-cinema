import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Crosshair, Loader2, Trash2 } from "lucide-react";

import {
  ApiError,
  deleteEntry,
  updateEntry,
  type FilmDetail,
  type SubtitleEntry,
} from "@/api/client";
import { Button } from "@/components/ui/button";
import { formatTimecode, parseTimecode } from "@/lib/timecode";

type EntryEditorProps = {
  filmId: string;
  entry: SubtitleEntry;
  onSeek: (timestampUs: number) => void;
};

export function EntryEditor({ filmId, entry, onSeek }: EntryEditorProps) {
  const queryClient = useQueryClient();
  const [prevEntry, setPrevEntry] = useState(entry);
  const [text, setText] = useState(entry.text);
  const [start, setStart] = useState(formatTimecode(entry.start_us));
  const [end, setEnd] = useState(formatTimecode(entry.end_us));
  const [problem, setProblem] = useState<string | null>(null);

  if (entry !== prevEntry) {
    setPrevEntry(entry);
    setText(entry.text);
    setStart(formatTimecode(entry.start_us));
    setEnd(formatTimecode(entry.end_us));
    setProblem(null);
  }

  const save = useMutation({
    mutationFn: (payload: { text: string; startUs: number; endUs: number }) =>
      updateEntry(filmId, entry.id, {
        text: payload.text,
        start_us: payload.startUs,
        end_us: payload.endUs,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData<FilmDetail>(["films", filmId], (current) =>
        current
          ? {
              ...current,
              entries: current.entries.map((item) => (item.id === updated.id ? updated : item)),
            }
          : current,
      );
    },
  });

  const remove = useMutation({
    mutationFn: () => deleteEntry(filmId, entry.id),
    onSuccess: () => {
      queryClient.setQueryData<FilmDetail>(["films", filmId], (current) =>
        current
          ? { ...current, entries: current.entries.filter((item) => item.id !== entry.id) }
          : current,
      );
    },
  });

  const parsedStart = parseTimecode(start);
  const parsedEnd = parseTimecode(end);
  const timingValid =
    parsedStart !== null && parsedEnd !== null && parsedEnd > parsedStart && text.trim().length > 0;

  const dirty =
    text !== entry.text ||
    parsedStart !== entry.start_us ||
    parsedEnd !== entry.end_us;

  function handleSave() {
    if (parsedStart === null || parsedEnd === null) {
      setProblem("Use a timecode such as 00:01:23.500.");
      return;
    }
    if (parsedEnd <= parsedStart) {
      setProblem("The end time must be after the start time.");
      return;
    }
    if (!text.trim()) {
      setProblem("Subtitle text cannot be empty.");
      return;
    }
    setProblem(null);
    save.mutate({ text: text.trim(), startUs: parsedStart, endUs: parsedEnd });
  }

  const mutationError = save.error ?? remove.error;
  const errorMessage =
    problem ??
    (mutationError instanceof ApiError
      ? mutationError.message
      : mutationError
        ? "The change could not be saved."
        : null);

  return (
    <li className="space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="timecode rounded bg-secondary px-2 py-0.5 text-xs text-muted-foreground">
            {String(entry.sequence + 1).padStart(2, "0")}
          </span>
          <span className="text-xs text-muted-foreground">
            {entry.source === "ocr" ? "OCR draft" : "Manual"}
            {entry.review_status === "reviewed" ? " · reviewed" : " · not reviewed"}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => onSeek(entry.start_us)}
            title="Play the film from this subtitle"
          >
            <Crosshair aria-hidden="true" className="size-4" />
            Play from here
          </Button>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            aria-label={`Delete subtitle ${entry.sequence + 1}`}
            title="Delete this subtitle"
            disabled={remove.isPending}
            onClick={() => {
              if (
                window.confirm(
                  "Delete this subtitle? The original OCR evidence stays in the database.",
                )
              ) {
                remove.mutate();
              }
            }}
          >
            {remove.isPending ? (
              <Loader2 aria-hidden="true" className="size-4 animate-spin" />
            ) : (
              <Trash2 aria-hidden="true" className="size-4" />
            )}
          </Button>
        </div>
      </div>

      <label className="block">
        <span className="sr-only">Subtitle text for entry {entry.sequence + 1}</span>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={2}
          maxLength={2000}
          className="w-full resize-y rounded-md border border-input bg-background px-3 py-2 font-serif text-base leading-6"
        />
      </label>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-xs text-muted-foreground">Start</span>
          <input
            value={start}
            onChange={(event) => setStart(event.target.value)}
            spellCheck={false}
            className="timecode h-9 w-full rounded-md border border-input bg-background px-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs text-muted-foreground">End</span>
          <input
            value={end}
            onChange={(event) => setEnd(event.target.value)}
            spellCheck={false}
            className="timecode h-9 w-full rounded-md border border-input bg-background px-2 text-sm"
          />
        </label>
      </div>

      {errorMessage ? (
        <p role="alert" className="text-xs leading-5 text-danger">
          {errorMessage}
        </p>
      ) : null}

      <div className="flex items-center gap-2">
        <Button
          type="button"
          size="sm"
          onClick={handleSave}
          disabled={!dirty || !timingValid || save.isPending}
        >
          {save.isPending ? (
            <Loader2 aria-hidden="true" className="size-4 animate-spin" />
          ) : (
            <Check aria-hidden="true" className="size-4" />
          )}
          Save entry
        </Button>
        {save.isSuccess && !dirty ? (
          <span className="text-xs text-verified" aria-live="polite">
            Saved
          </span>
        ) : null}
      </div>
    </li>
  );
}
