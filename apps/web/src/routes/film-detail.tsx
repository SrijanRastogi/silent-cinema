import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Clock,
  Download,
  Film,
  Layers,
  Loader2,
  Pause,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  RotateCw,
  Video,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import {
  ApiError,
  burnedVideoDownloadUrl,
  createEntry,
  filmVideoUrl,
  muxedVideoDownloadUrl,
  scanFilm,
  subtitleDownloadUrl,
  type FilmDetail,
} from "@/api/client";
import { filmQueryOptions } from "@/api/queries";
import { EntryEditor } from "@/components/entry-editor";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBytes, formatDuration, formatRecordedAt } from "@/lib/format";
import { activeEntryIndex, formatTimecode, parseTimecode } from "@/lib/timecode";

export function FilmDetailPage() {
  const { filmId } = useParams<{ filmId: string }>();
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [currentPositionUs, setCurrentPositionUs] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isAddingEntry, setIsAddingEntry] = useState<boolean>(false);
  const [newText, setNewText] = useState("");
  const [newStart, setNewStart] = useState("");
  const [newEnd, setNewEnd] = useState("");
  const [newEntryError, setNewEntryError] = useState<string | null>(null);
  const [scanLanguage, setScanLanguage] = useState("eng");

  const filmQuery = useQuery(filmQueryOptions(filmId ?? ""));
  const film = filmQuery.data;

  const entries = film?.entries ?? [];
  const activeIndex = entries.length > 0 ? activeEntryIndex(entries, currentPositionUs) : -1;
  const activeEntry = activeIndex >= 0 ? entries[activeIndex] : null;

  // Scan mutation
  const scanMutation = useMutation({
    mutationFn: () => scanFilm(filmId ?? "", scanLanguage),
    onSuccess: (updatedFilm) => {
      queryClient.setQueryData<FilmDetail>(["films", filmId], updatedFilm);
      void queryClient.invalidateQueries({ queryKey: ["films"] });
    },
  });

  // Create manual entry mutation
  const addMutation = useMutation({
    mutationFn: (payload: { text: string; startUs: number; endUs: number }) =>
      createEntry(filmId ?? "", {
        text: payload.text,
        start_us: payload.startUs,
        end_us: payload.endUs,
      }),
    onSuccess: (created) => {
      queryClient.setQueryData<FilmDetail>(["films", filmId], (current) =>
        current
          ? {
              ...current,
              entries: [...current.entries, created].sort((a, b) => a.start_us - b.start_us),
            }
          : current,
      );
      setIsAddingEntry(false);
      setNewText("");
      setNewEntryError(null);
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setNewEntryError(err.message);
      } else {
        setNewEntryError("Failed to create entry.");
      }
    },
  });

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentPositionUs(Math.round(videoRef.current.currentTime * 1_000_000));
    }
  };

  const handleSeek = (timestampUs: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestampUs / 1_000_000;
      void videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      void videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const stepSeconds = (seconds: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime + seconds);
  };

  const openAddForm = () => {
    const startUs = currentPositionUs;
    const endUs = currentPositionUs + 3_000_000; // default 3s duration
    setNewStart(formatTimecode(startUs));
    setNewEnd(formatTimecode(endUs));
    setNewText("");
    setNewEntryError(null);
    setIsAddingEntry(true);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsedStart = parseTimecode(newStart);
    const parsedEnd = parseTimecode(newEnd);

    if (parsedStart === null || parsedEnd === null) {
      setNewEntryError("Invalid timecode format. Use HH:MM:SS.mmm.");
      return;
    }
    if (parsedEnd <= parsedStart) {
      setNewEntryError("End time must be after start time.");
      return;
    }
    if (!newText.trim()) {
      setNewEntryError("Subtitle text cannot be empty.");
      return;
    }

    addMutation.mutate({
      text: newText.trim(),
      startUs: parsedStart,
      endUs: parsedEnd,
    });
  };

  // Scroll active entry into view if playing
  useEffect(() => {
    if (activeEntry && isPlaying) {
      const el = document.getElementById(`entry-${activeEntry.id}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }
  }, [activeEntry, isPlaying]);

  if (filmQuery.isPending) {
    return (
      <div className="flex h-64 items-center justify-center space-x-3 text-muted-foreground">
        <Loader2 className="size-6 animate-spin text-primary" />
        <p className="text-sm">Loading film reel and subtitles...</p>
      </div>
    );
  }

  if (filmQuery.isError || !film) {
    return (
      <div role="alert" className="film-gate px-6 py-10">
        <p className="text-lg font-medium text-danger">Film could not be loaded.</p>
        <p className="mt-2 text-sm text-muted-foreground">
          {filmQuery.error instanceof ApiError
            ? filmQuery.error.message
            : "The requested film could not be found or the server returned an error."}
        </p>
        <div className="mt-6">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-primary hover:underline">
            <ArrowLeft className="size-4" />
            Back to workspace
          </Link>
        </div>
      </div>
    );
  }

  const durationUs = film.duration_us ?? 0;
  const progressRatio = durationUs > 0 ? Math.min(1, currentPositionUs / durationUs) : 0;

  return (
    <div className="space-y-8">
      {/* Top Breadcrumb & Metadata Header */}
      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          Back to films
        </Link>
        <div className="mt-2 flex flex-wrap items-baseline justify-between gap-4">
          <div>
            <h1 className="text-3xl font-medium tracking-tight text-foreground">
              {film.original_filename}
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="timecode font-mono text-primary">
                {formatDuration(film.duration_us)}
              </span>
              {film.width && film.height && <span>· {film.width}×{film.height}</span>}
              <span>· {formatBytes(film.byte_size)}</span>
              <span>· Uploaded {formatRecordedAt(film.created_at)}</span>
              <Badge variant={film.entries.length > 0 ? "verified" : "warning"}>
                {film.entries.length} {film.entries.length === 1 ? "subtitle" : "subtitles"}
              </Badge>
            </div>
          </div>

          {/* Quick Export Actions */}
          <div className="flex flex-wrap items-center gap-2">
            <a
              href={subtitleDownloadUrl(film.id, "srt")}
              download
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary/80"
              title="Download standard SubRip Subtitle file"
            >
              <Download className="size-3.5 text-primary" />
              SRT
            </a>
            <a
              href={subtitleDownloadUrl(film.id, "vtt")}
              download
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary/80"
              title="Download WebVTT file"
            >
              <Download className="size-3.5 text-primary" />
              WebVTT
            </a>
            <a
              href={muxedVideoDownloadUrl(film.id)}
              download
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary/80"
              title="Download Matroska video with soft subtitles muxed"
            >
              <Film className="size-3.5 text-primary" />
              Muxed MKV
            </a>
            <a
              href={burnedVideoDownloadUrl(film.id)}
              download
              className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary/80"
              title="Download MP4 with subtitles permanently burned onto video"
            >
              <Video className="size-3.5 text-primary" />
              Burned MP4
            </a>
          </div>
        </div>
      </div>

      {/* Main Grid: Video Player + Subtitle Editor */}
      <div className="grid gap-8 lg:grid-cols-12">
        {/* Left: Video Player with Subtitle Overlay */}
        <div className="space-y-4 lg:col-span-7">
          <Card className="overflow-hidden border border-border bg-black shadow-lg">
            <div className="relative aspect-video w-full bg-black">
              <video
                ref={videoRef}
                src={filmVideoUrl(film.id)}
                onTimeUpdate={handleTimeUpdate}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                className="h-full w-full object-contain"
                crossOrigin="anonymous"
              >
                <track
                  kind="subtitles"
                  label="Generated Subtitles"
                  srcLang="en"
                  src={subtitleDownloadUrl(film.id, "vtt")}
                  default
                />
              </video>

              {/* Live Synchronized Subtitle Overlay on Video */}
              {activeEntry && (
                <div className="pointer-events-none absolute inset-x-0 bottom-6 flex justify-center px-6">
                  <div className="max-w-2xl rounded-md bg-black/80 px-4 py-2 text-center shadow-md backdrop-blur-sm border border-white/10">
                    <p className="font-serif text-lg leading-relaxed text-amber-100 sm:text-xl">
                      {activeEntry.text}
                    </p>
                    <span className="mt-1 block font-mono text-[10px] text-muted-foreground">
                      {formatTimecode(activeEntry.start_us)} → {formatTimecode(activeEntry.end_us)}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Custom Interactive Player Bar */}
            <div className="border-t border-border/40 bg-card p-4 space-y-3">
              {/* Timeline with cue markers */}
              <div className="relative h-2 w-full cursor-pointer rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${progressRatio * 100}%` }}
                />
                {/* Marker points for each intertitle interval */}
                {durationUs > 0 &&
                  film.entries.map((entry) => {
                    const leftPercent = (entry.start_us / durationUs) * 100;
                    const widthPercent = Math.max(0.5, ((entry.end_us - entry.start_us) / durationUs) * 100);
                    return (
                      <div
                        key={entry.id}
                        onClick={() => handleSeek(entry.start_us)}
                        title={`${formatTimecode(entry.start_us)}: ${entry.text.slice(0, 30)}...`}
                        className="absolute top-0 h-2 bg-amber-400/70 hover:bg-amber-300"
                        style={{ left: `${leftPercent}%`, width: `${widthPercent}%` }}
                      />
                    );
                  })}
              </div>

              {/* Player Controls */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={togglePlay}
                    aria-label={isPlaying ? "Pause" : "Play"}
                  >
                    {isPlaying ? <Pause className="size-5" /> : <Play className="size-5" />}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => stepSeconds(-5)}
                    title="Rewind 5 seconds"
                  >
                    <RotateCcw className="size-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => stepSeconds(5)}
                    title="Forward 5 seconds"
                  >
                    <RotateCw className="size-4" />
                  </Button>
                  <div className="font-mono text-xs text-muted-foreground ml-2">
                    <span className="text-foreground">{formatTimecode(currentPositionUs)}</span>
                    {" / "}
                    <span>{formatTimecode(durationUs)}</span>
                  </div>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={openAddForm}
                  className="gap-1.5"
                >
                  <Plus className="size-4" />
                  Add Subtitle at Timestamp
                </Button>
              </div>
            </div>
          </Card>

          {/* Re-scan Card */}
          <Card className="border border-border">
            <CardHeader className="py-4">
              <CardTitle className="text-base flex items-center gap-2">
                <RefreshCw className="size-4 text-primary" />
                Intertitle Detection & OCR Scanning
              </CardTitle>
              <CardDescription className="text-xs">
                Scan or re-scan the reel with FFmpeg intertitle card detection and Tesseract OCR.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="text"
                  value={scanLanguage}
                  onChange={(e) => setScanLanguage(e.target.value.trim())}
                  disabled={scanMutation.isPending}
                  placeholder="Language (e.g. eng)"
                  className="font-mono h-9 w-32 rounded-md border border-input bg-background px-2.5 text-xs"
                />
                <Button
                  type="button"
                  size="sm"
                  disabled={scanMutation.isPending}
                  onClick={() => scanMutation.mutate()}
                  className="gap-1.5"
                >
                  {scanMutation.isPending ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <RefreshCw className="size-3.5" />
                  )}
                  {scanMutation.isPending ? "Scanning frames & OCR..." : "Run Scanner"}
                </Button>
                {scanMutation.isSuccess && (
                  <span className="text-xs text-verified">Scan completed</span>
                )}
                {scanMutation.isError && (
                  <span className="text-xs text-danger">
                    {scanMutation.error instanceof ApiError
                      ? scanMutation.error.message
                      : "Scan failed"}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Subtitle Timeline Entries List */}
        <div className="space-y-4 lg:col-span-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="size-4 text-primary" />
              <h2 className="text-lg font-medium text-foreground">Subtitle Entries</h2>
            </div>
            <span className="text-xs text-muted-foreground font-mono">
              {film.entries.length} total
            </span>
          </div>

          {/* Manual Entry Form */}
          {isAddingEntry && (
            <Card className="border-primary/50 bg-secondary/20 p-4">
              <form onSubmit={handleCreateSubmit} className="space-y-3">
                <h3 className="text-sm font-medium">New Subtitle Entry</h3>
                <textarea
                  value={newText}
                  onChange={(e) => setNewText(e.target.value)}
                  placeholder="Enter subtitle text..."
                  rows={2}
                  className="w-full rounded-md border border-input bg-background p-2 font-serif text-sm"
                  autoFocus
                />
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  <div>
                    <label className="text-muted-foreground">Start Time</label>
                    <input
                      value={newStart}
                      onChange={(e) => setNewStart(e.target.value)}
                      className="mt-1 h-8 w-full rounded border border-input bg-background px-2"
                    />
                  </div>
                  <div>
                    <label className="text-muted-foreground">End Time</label>
                    <input
                      value={newEnd}
                      onChange={(e) => setNewEnd(e.target.value)}
                      className="mt-1 h-8 w-full rounded border border-input bg-background px-2"
                    />
                  </div>
                </div>
                {newEntryError && <p className="text-xs text-danger">{newEntryError}</p>}
                <div className="flex items-center gap-2 pt-1">
                  <Button type="submit" size="sm" disabled={addMutation.isPending}>
                    {addMutation.isPending ? "Adding..." : "Add Subtitle"}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsAddingEntry(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Subtitle List */}
          {film.entries.length === 0 ? (
            <Card className="p-8 text-center border-dashed">
              <Clock className="mx-auto size-8 text-muted-foreground/60" />
              <p className="mt-3 text-sm font-medium">No subtitles detected yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Run the scanner to extract intertitles or add subtitles manually.
              </p>
            </Card>
          ) : (
            <ul className="space-y-3 max-h-[750px] overflow-y-auto pr-1">
              {film.entries.map((entry, index) => {
                const isActive = activeIndex === index;
                return (
                  <div
                    key={entry.id}
                    id={`entry-${entry.id}`}
                    className={`rounded-lg border transition-all ${
                      isActive
                        ? "border-primary bg-primary/5 shadow-md ring-1 ring-primary/40"
                        : "border-border bg-card"
                    }`}
                  >
                    <EntryEditor
                      filmId={film.id}
                      entry={entry}
                      onSeek={handleSeek}
                    />
                  </div>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}