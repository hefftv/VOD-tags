# Process Flow

This page walks through the full highlight lifecycle from user action to clip playback.

## User journey (high level)

```mermaid
sequenceDiagram
  actor User
  participant Web as Django Web App
  participant Helix as Twitch Helix
  participant ML as ML Server
  participant Store as Clip Storage
  participant Browser as Browser Player

  User->>Web: Login
  User->>Web: Submit channel name
  Web->>Helix: Resolve channel / latest VOD name
  Web->>Web: Save Stream to SQLite
  Web->>ML: GET /process_stream
  Note over ML: Record + detect + score loop
  ML->>Store: Publish clip MP4
  ML->>Web: GET /add_clip?clip_link=...
  Web->>Web: Save StreamHighlight
  User->>Web: Open stream page
  Web->>User: Render clip list
  User->>Browser: Play clip URL
  Browser->>Store: Fetch MP4
```

## Phase 1 — Add stream (web app)

Triggered when a logged-in user submits a Twitch channel name on the dashboard.

```mermaid
flowchart TD
  A[User POST /add_stream/] --> B[Twitch Helix lookup]
  B --> C[Create Stream row in SQLite]
  C --> D["GET http://{ML_SERVER}/process_stream"]
  D --> E[Redirect to dashboard]
  D -.->|timeout/errors ignored| E
```

**Inputs:** `stream_link` (channel name), authenticated username  
**Outputs:** `Stream` record; fire-and-forget ML trigger

Relevant code: `webapp/viewer/views.py` → `add_stream()`

## Phase 2 — Start processing (ML server)

The ML server receives `/process_stream` and starts a long-running pipeline for that channel.

```mermaid
flowchart TD
  A[GET /process_stream] --> B[Generate stream UUID]
  B --> C[Start twitch-recorder subprocess]
  C --> D{Recording file exists?}
  D -->|poll every 1s| D
  D -->|yes| E[Start HighlightDetector process]
  E --> F[Prediction loop every 30s]
```

**Recording path:** `{STREAMS_ROOT}/recorded/{channel}/{uuid}.mp4`  
**Requirement:** Target channel must be **live** on Twitch.

Relevant code: `server/server.py`, `server/processor.py` → `download_stream()`

## Phase 3 — Parallel feature extraction

Three detectors run concurrently while the recording grows:

```mermaid
flowchart TB
  subgraph detectors [HighlightDetector.start]
    chat[ChatDetector - IRC thread]
    move[MovementDetector - video thread]
    sound[SoundDetector - audio thread]
  end

  video[(Growing MP4 file)]
  irc[(Twitch chat)]

  irc --> chat
  video --> move
  video --> sound

  chat --> csvChat["{uuid}_chat.csv"]
  move --> csvMove["{uuid}_movement.csv"]
  sound --> csvSound["{uuid}_sound.csv"]
```

Each detector appends **10-second windows** to its CSV with timestamp-aligned features.

| Detector | Reads | Writes | Update cadence |
|----------|-------|--------|----------------|
| Chat | IRC messages | Sentiment counts | Per message / window |
| Movement | Video frames | Optical flow + CNN score | ~1s poll loop |
| Sound | Last seconds of audio | PANNs tags + loudness | ~1s poll loop |

See [ML Pipeline](ML-Pipeline) for feature column details.

## Phase 4 — Metamodel scoring (every 30s)

```mermaid
flowchart TD
  A[All 3 CSVs exist?] -->|no| skip[Skip this cycle]
  A -->|yes| B[Merge on start_time]
  B --> C[Apply standard_scaler.joblib]
  C --> D[model.joblib predict_proba]
  D --> E{Best unseen window with prob > 0.2?}
  E -->|no| skip
  E -->|yes| F[Compute ffmpeg start + 10s duration]
  F --> G[extract_time_frame]
  G --> H[publish_clip]
  H --> I[send_clip_to_webapp]
```

**Highlight selection rules:**

- Sort windows by predicted probability (descending)
- Skip windows already published
- Threshold: probability > **0.2**
- Clip length: **10 seconds**

Relevant code: `server/processor.py` → `check_predictions()`, `publish_clip()`

## Phase 5 — Clip publish

```mermaid
flowchart LR
  A[ffmpeg extracts segment] --> B{CLIP_STORAGE_BACKEND}
  B -->|gcp| C[gsutil cp to GCS]
  B -->|local| D[copy to /clips volume]
  C --> E[GCS public URL]
  D --> F[nginx URL]
  E --> G[Callback /add_clip]
  F --> G
```

| Backend | Public URL pattern |
|---------|-------------------|
| GCP | `https://storage.googleapis.com/{bucket}/{clip}.mp4` |
| Local | `http://localhost:8080/{clip}.mp4` |

## Phase 6 — Web callback and playback

```mermaid
sequenceDiagram
  participant ML as ML Server
  participant Web as Django
  participant DB as SQLite
  participant User as User Browser

  ML->>Web: GET /add_clip?user_name&stream_link&clip_link
  Web->>DB: INSERT StreamHighlight
  Web-->>ML: JSON status ok
  User->>Web: GET /stream/{id}
  Web->>DB: SELECT highlights for stream
  Web->>User: HTML with video tags
  User->>User: Browser loads clip_link MP4
```

The stream page renders each highlight as:

```html
<video src="{{ clip.clip_link }}"></video>
```

So `clip_link` must be a **browser-reachable** public URL.

## UI flow (screenshots)

### Login and add stream

![Add stream](https://raw.githubusercontent.com/hefftv/VOD-tags/main/images/add_stream.png)

### Stream appears on dashboard

![Stream appeared](https://raw.githubusercontent.com/hefftv/VOD-tags/main/images/stream_appeared.png)

### Highlights appear on stream page

![Highlights appeared](https://raw.githubusercontent.com/hefftv/VOD-tags/main/images/highlights_appeared.png)

## Timing diagram

```mermaid
gantt
  title Typical highlight pipeline timing
  dateFormat X
  axisFormat %S s

  section Recording
  Streamlink capture     :a1, 0, 3600

  section Features
  Chat CSV growing       :a2, 5, 3600
  Movement CSV growing   :a3, 10, 3600
  Sound CSV growing      :a4, 10, 3600

  section Scoring
  First score attempt    :milestone, 30, 0
  Score every 30s        :a5, 30, 3600

  section Clip
  ffmpeg extract ~10s    :a6, 35, 45
  Publish + callback     :a7, 45, 50
```

First highlights typically appear **after** all three feature CSVs exist and the first 30-second scoring cycle finds a window above threshold. Exact timing depends on stream length, model confidence, and infrastructure latency.

## Failure modes

| Symptom | Likely cause |
|---------|--------------|
| Stream added but no clips | Channel offline; ML unreachable; missing Twitch creds |
| Clips in DB but won't play | `clip_link` not public / wrong `CLIP_PUBLIC_BASE_URL` |
| No chat features | Invalid `TWITCH_OAUTH_TOKEN` or nickname |
| GCP clips fail | Missing `gsutil`, bucket permissions, or private bucket |

See [Configuration](Configuration) and [Deployment](Deployment) for environment-specific setup.
