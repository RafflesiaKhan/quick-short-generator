# Feature: Video Generation Pipeline
**Status:** active
**Version:** 1.0
**Owner:** @RafflesiaKhan
**Last Updated:** 2026-03-17

## Objective
Accept 1–6 user-uploaded images each paired with a text prompt, route each
image-prompt pair to the selected AI video provider (Kling AI or Minimax),
poll until each segment is ready, merge all segments into a single MP4 file
using a background task, and make the final video available for playback and
download — all within a single FastAPI + React web application.

## Acceptance Criteria
1. User can upload between 1 and 6 images via drag-and-drop or file picker; uploads outside this range are rejected with a clear error message before submission
2. Each uploaded image must have a corresponding non-empty text prompt; the Generate button remains disabled and an inline error is shown per missing prompt
3. User can select either Kling AI or Minimax as the video generation provider before initiating generation
4. When Dev Mode is OFF, the user must supply valid API credentials for the chosen provider; the form validates that all required credential fields are non-empty before allowing submission
5. When Dev Mode is ON, credentials are sourced exclusively from backend environment variables (`KLINGAI_ACCESS_KEY_ID` / `KLINGAI_ACCESS_KEY_SECRET` for Kling; `MINIMAX_API_KEY` / `MINIMAX_GROUP_ID` for Minimax) and the credential input fields are hidden from the UI
6. On submission, the backend returns a `video_id` immediately; the frontend begins polling `HEAD /video/{video_id}` at a regular interval and displays a loading / in-progress state to the user
7. Each image-prompt pair is sent independently to the selected AI provider and generates a separate video segment of approximately 10 seconds
8. Kling AI requests use JWT authentication (generated from Access Key ID + Secret) and send image data as Base64-encoded strings
9. Minimax requests use the API Key and Group ID as authentication parameters
10. All generated video segments are downloaded to the server and merged into a single `{video_id}.mp4` file using Moviepy, executed as a FastAPI BackgroundTask so it does not block the API response
11. Once the merged file exists on the server, `HEAD /video/{video_id}` returns HTTP 200; the frontend stops polling, renders an inline video player with the final video, and enables the Download MP4 button
12. If any individual AI provider call fails (network error, auth error, quota exceeded), the backend returns a structured error response and the frontend displays a human-readable error message without crashing

## Out of Scope
- OAuth or social login — no user accounts in this version
- Persistent video storage or history — merged files are stored temporarily on the server only
- Video editing post-generation (trimming, reordering segments, overlays, music)
- Third-party providers beyond Kling AI and Minimax (RunwayML, Pika Labs, etc.) — tracked as future improvements
- Negative prompts or style reference parameters — not exposed in this version
- Cost estimation or API usage tracking in the UI
- Configurable video length — all segments are fixed at ~10 seconds

## Edge Cases
- User uploads 0 images and clicks Generate — rejected client-side before API call
- User uploads 7 or more images — excess images rejected with a clear count error
- One or more prompt fields left empty at submission time — per-image inline validation error shown, generation blocked
- Dev Mode is ON but environment variables are missing or empty — backend returns a 500 with a clear "missing credentials" message; frontend surfaces it
- AI provider returns an error mid-batch (e.g. segment 3 of 5 fails) — entire generation job fails; frontend shows which segment failed if the API provides that context
- Merged video file takes longer than expected — frontend continues polling indefinitely until success or explicit error response; no client-side timeout in v1
- User navigates away during polling — generation continues on the server; video is not retrievable unless the user retains the video_id (no persistence in v1)
- Uploaded image format unsupported by the provider — backend surfaces the provider error message to the frontend

## Integrations
- **Called by:** React frontend (`POST /generate-video`, `POST /upload-images`, `HEAD /video/{video_id}`)
- **Calls:** Kling AI external API (via `klingai_client.py`), Minimax external API (via `minimax_client.py`)
- **Uses:** Moviepy for video merging (BackgroundTask), PyJWT for Kling auth token generation
- **Storage:** Local filesystem (`backend/uploads/`) for temporary image and video segment storage

## API Contracts

### POST /upload-images
```
Input (multipart/form-data):
  files: File[]   — 1 to 6 image files

Output (200):
  { image_ids: string[] }

Errors:
  400 — fewer than 1 or more than 6 images supplied
  422 — malformed request body
```

### GET /api-providers
```
Output (200):
  { providers: Array<{ id: string, name: string }> }
  Example: [{ id: "kling", name: "Kling AI" }, { id: "minimax", name: "Minimax" }]
```

### POST /generate-video
```
Input (JSON):
  {
    image_ids:    string[],         — references from /upload-images
    prompts:      string[],         — one per image, same order, all non-empty
    provider:     "kling" | "minimax",
    credentials?: {
      kling?:    { access_key_id: string, access_key_secret: string },
      minimax?:  { api_key: string, group_id: string }
    }
  }

Output (200):
  { video_id: string }              — UUID for polling

Errors:
  400 — prompt count does not match image count
  400 — required credentials missing and Dev Mode is OFF
  500 — provider authentication failure
  502 — upstream AI provider error
```

### HEAD /video/{video_id}
```
Output:
  200 — merged video file exists and is ready
  404 — file not yet ready or video_id unknown

Notes:
  Frontend polls this endpoint. No body is returned (HEAD).
  When 200 is received, frontend loads GET /video/{video_id} for playback.
```

### GET /video/{video_id}
```
Output (200):
  MP4 file stream (Content-Type: video/mp4)

Errors:
  404 — video_id not found or file not yet generated
```