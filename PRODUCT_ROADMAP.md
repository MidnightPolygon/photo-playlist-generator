# Photo Playlist Generator — Product Roadmap

**Roadmap version:** Draft v1.2 (approved)  
**Project:** Photo Playlist Generator  
**Repository:** `MidnightPolygon/photo-playlist-generator`  
**Platform:** Python, Streamlit, Google Gemini  
**Product direction:** Photo-inspired media discovery, with Music first and Audiobooks later  
**Initial public demo target:** October 18, 2026

> This roadmap records approved product direction and planned capabilities. Feature priorities and milestone sequencing are planning guidance, not a claim that every item is implemented.

## 1. Product vision

Photo Playlist Generator turns photographs into personalized media recommendations. Users upload a photo, optionally add keywords or preferences, and receive recommendations inspired by the image's setting, atmosphere, and emotional tone.

The product will evolve into **one unified application** with two discovery modes:

- **Music:** Generate, refine, save, and eventually export playlists to streaming services.
- **Audiobooks:** Discover books inspired by photographs, refine recommendation lists, and follow links to audiobook and book services.

Both modes should reuse image processing, AI orchestration, history, metadata validation, and responsive navigation wherever practical. The product name remains **Photo Playlist Generator** for now.

## 2. Current prototype baseline

The existing Streamlit prototype provides or has demonstrated:

- Single-photo upload with JPEG, PNG, and WebP support.
- Optional mood/context keywords in the generation workflow.
- Gemini-powered image interpretation and music recommendations.
- AI-generated playlist titles, artist/title recommendations, and explanations.
- Playlist size controls: **5–50 songs**, or target duration of **30–180 minutes**.
- Custom slider with labeled ticks, value bubble, and duration formatting.
- Expandable track rows with reasons for each selection.
- Track duration and calculated playlist total.
- Image optimization before AI processing.
- Session-state playlist persistence across UI control changes.
- Spotify and YouTube Music search links.
- Public deployment on Streamlit Community Cloud and desktop/mobile testing.

**Known areas for improvement:** photo upload/reset reliability, mobile regressions, playlist duration accuracy, consistent photo influence, robust error handling, and track metadata verification.

## 3. Product principles

1. **The photo leads.** Recommendations must meaningfully reflect the uploaded image, not simply repeat generic mood playlists.
2. **Preferences refine, not replace, the image.** Keywords, genres, and discovery controls guide results while retaining photo influence.
3. **Users retain control.** Recommendations, playlist names, and tracks should be editable.
4. **No unnecessary AI calls.** Restore saved session results and perform local edits without regenerating when possible.
5. **Verify before promising.** Track/book metadata and provider integrations must be validated; search links are not equivalent to authenticated playlist creation.
6. **Mobile is a first-class experience.** Desktop and narrow-screen layouts should remain usable.
7. **Ship music reliability first.** Audiobook expansion follows a stable music MVP.

## 4. Music roadmap

### 4.1 P0 — Reliability and MVP readiness

| ID | Feature | Acceptance direction |
|---|---|---|
| **PL-016** | Photo uploader reset bug | Resolve upload/reset behavior, especially mobile timing and state transitions; test on desktop and mobile. |
| **PL-014** | Compact photo thumbnail | Show a compact thumbnail of the image associated with the current playlist without overwhelming the interface. |
| **PL-015** | “What the AI Saw” | Provide an understandable explanation of the image characteristics that informed the playlist. |
| — | Photo influence validation | Test photo-only and photo-plus-keyword generation for meaningful, reproducible image relevance. |
| — | Duration reliability | Improve total-duration targeting, correction behavior, and accurate recalculation. |
| — | Error handling and API safeguards | Handle upload, model, parsing, timeout, and quota failures gracefully; protect API keys and avoid excessive calls. |
| — | Mobile regression coverage | Validate upload, generation, sliders, display, and navigation on supported mobile browsers. |

### 4.2 P1 — Music personalization

**Optional keywords:** A photograph alone must be sufficient to generate a playlist. Empty keywords should be treated as intentional photo-only input, not a validation error.

**Genre controls:** Provide multi-select toggles for the following 12 genres:

- Rock
- Pop
- Hip-Hop
- Electronic
- Indie
- Alternative
- R&B / Soul
- Jazz
- Blues
- Country
- Classical
- Ambient

Include an **Other** toggle that reveals a comma-separated free-text field for additional genres. Genre selections should influence, not override, the photograph.

**Familiarity / discovery slider:** Let users choose between familiar, recognizable selections and more exploratory recommendations.

**Editable playlist name:** Display the AI-generated name with a pencil/edit control. Editing exposes **Save** and **Cancel** actions; saving does not require another AI generation call.

**Generation control:** Retain the existing **Generate Playlist** action for initial generation and regeneration. Do **not** add a separate redundant Regenerate button.

### 4.3 P1 — Playlist editing

| Action | Expected behavior |
|---|---|
| **Remove** | Delete the selected track from the current playlist. |
| **Add** | Let users manually add tracks initially; AI-assisted additions may follow later. |
| **Swap** | Offer **three AI-recommended alternatives** to a selected track, each with thumbs-up/down feedback. |

**Swap acceptance rules:**

- **0 accepted:** Keep the original track; allow the user to request more alternatives.
- **1 accepted:** Replace the original with the one accepted track.
- **2 accepted:** Replace the original with both accepted tracks; playlist grows by one.
- **3 accepted:** Replace the original with all three accepted tracks; playlist grows by two.

After **every edit**, recalculate total playlist duration. Generation duration is a target, not a constraint that prevents intentional user edits from changing length.

### 4.4 P1/P2 — Export, verification, and history

**Export:** Support copying playlist details and downloading them in **CSV** and plain-text formats.

**Track verification:** Improve confidence that recommended artist/title combinations exist and can be found on the intended services. Clearly handle unavailable or ambiguous tracks.

**Recent playlist history:** Keep the **five most recent playlists** in Streamlit session state, including thumbnails and subsequent edits.

- **Wide screens:** Display history in a right-hand sidebar alongside the generator.
- **Narrow/mobile screens:** Use a collapsed dropdown above the generator.
- **Restore:** Selecting an entry restores that playlist and its edits **without a new Gemini call**.
- Session history is not a promise of permanent cross-device storage.

### 4.5 P2 — Streaming integration

**Provider order:** YouTube Music first, Spotify later.

The desired workflow is to authenticate with a supported provider, then either:

1. Create a new playlist in the user's account; or
2. Append the generated songs to an existing playlist.

**Duplicate handling:** Skip tracks already present in the destination playlist. For example, adding 10 tracks to a 15-track playlist with 3 duplicates should append only **7 unique tracks**.

Provider API access, authentication requirements, playlist-writing capabilities, and terms must be validated before implementation commitments. Until then, provider **search links** remain the fallback; a link is not a completed playlist export.

## 5. Audiobook expansion

Audiobooks are a **later product mode**, not a prerequisite for the initial music MVP. The user experience should translate photo-driven discovery into recommendations of books available in audiobook form.

| ID | Feature | Scope |
|---|---|---|
| **AB-001** | Photo-to-audiobook recommendation engine | Interpret the image and recommend relevant audiobook titles with explanations. |
| **AB-002** | Literary genres | Allow genre preferences appropriate to books and audiobooks. |
| **AB-003** | Count and duration controls | Let users shape recommendation count and listening-time preferences where reliable metadata permits. |
| **AB-004** | Metadata verification | Verify book title, author, audiobook edition, narrator, and duration when available. |
| **AB-005** | Audible integration | Start with verified listing/search links; authenticated actions only if permitted. |
| **AB-006** | Libro.fm integration | Start with verified listing/search links; authenticated actions only if permitted. |
| **AB-007** | Goodreads integration | Provide appropriate book discovery/listing links; validate any deeper integration. |
| **AB-008** | Audiobook list editing | Remove, add, and replace audiobook recommendations. |
| **AB-009** | Audiobook history | Restore recent audiobook recommendation lists using the shared history model. |

**Integration boundary:** Audible, Libro.fm, and Goodreads should initially be treated as **discovery/link destinations**. Do not promise direct library additions, purchases, or account modifications until provider APIs and permissions are confirmed.

## 6. Shared platform capabilities

| ID | Feature | Scope |
|---|---|---|
| **CORE-001** | Music / Audiobooks selector | Two modes within one app; music remains the initial/default experience. |
| **CORE-002** | Shared photo and AI processing | Reuse upload validation, image optimization, prompting infrastructure, and error handling. |
| **CORE-003** | Shared history | Common session-history mechanics with mode-specific stored recommendations. |
| **CORE-004** | Metadata and provider links | Reusable validation, external link handling, and provider capability boundaries. |
| **CORE-005** | Responsive navigation | Consistent desktop/mobile navigation, including mode selection and history placement. |

## 7. Releases, versioning, and feedback

| ID | Feature | Scope |
|---|---|---|
| **PL-017** | Application footer | Show app version, release notes access, and a feedback entry point. |
| **PL-018** | Version and release management | Maintain `CHANGELOG.md`, semantic or otherwise consistent version identifiers, Git tags, and GitHub Releases. |
| **PL-019** | Feedback capture | Store submitted feedback in a **separate private GitHub repository**, not the public app repository. |

Feedback collection must not expose private repository credentials or write tokens in the client. Validate the chosen storage method and abuse protections before release.

## 8. Milestone sequence

Milestones are **ordered planning stages**, not fixed calendar promises.

| Milestone | Outcome |
|---|---|
| **M1 — Public demo stability** | Resolve critical upload/mobile issues, protect API calls, and maintain a dependable generation flow. |
| **M2 — Photo transparency** | Compact photo thumbnail, “What the AI Saw,” and stronger photo-influence testing. |
| **M3 — Personalization** | Photo-only generation, genre multi-select with Other, discovery slider, and editable playlist title. |
| **M4 — Playlist control** | Remove, manual Add, three-option Swap, and accurate duration updates. |
| **M5 — Portability and trust** | CSV/text export, copy action, and track verification. |
| **M6 — Recent history** | Five-entry session history, responsive placement, and restore without AI regeneration. |
| **M7 — Music service integration** | Validate YouTube Music first, then Spotify; support new/append flows where feasible and skip duplicates. |
| **M8 — Release and feedback system** | Footer, versioning, changelog, GitHub releases, and private feedback storage. |
| **M9 — Unified media foundation** | Introduce mode selector and shared components while preserving music behavior. |
| **M10 — Audiobook discovery** | Deliver photo-driven audiobook recommendations, verification, editing, history, and provider listing links. |

**Priority rule:** Finish and validate the music MVP before expanding into audiobooks. Revisit sequence based on tester feedback and provider feasibility.

## 9. Testing and validation

- Test on desktop and mobile, including Pixel and Samsung browsers.
- Test photo-only, keyword-guided, genre-guided, and mixed-input generation.
- Verify uploaded photo remains associated with the displayed playlist and restored history entry.
- Compare requested versus actual playlist duration and check every edit's recalculation.
- Test Swap acceptance counts of 0, 1, 2, and 3.
- Confirm playlist history restores locally without making a model call.
- Confirm exports preserve title, artist, duration, and available explanations.
- Confirm duplicate filtering when appending to a provider playlist.
- Validate provider links and metadata before claiming availability.
- Check failure paths: missing/invalid uploads, model errors, malformed responses, and API rate limits.
- Collect qualitative feedback from prototype testers and prioritize observed usability issues.

## 10. Explicitly deferred or conditional

- A separate **Regenerate** button: **not planned**; the existing Generate Playlist action covers regeneration.
- Permanent user accounts and cloud-synced history: **not part of the current five-entry session-history commitment**.
- AI-assisted Add suggestions: **later enhancement**; manual Add first.
- Embedded music playback, background playback, or a standalone streaming platform: **longer-term exploration**, not an MVP promise.
- Direct audiobook-provider account actions: **conditional on documented API support and authorization**.
- Formal developer-environment setup documentation: **deferred**.
- Renaming the product: **not approved**.

## 11. Roadmap governance

This document represents the **approved Draft v1.2 product direction**. New ideas should be explored and evaluated separately before being added as roadmap commitments. Implementation details belong in development work, with roadmap changes reflecting approved decisions rather than speculative features.

**Suggested next repository artifacts:** `CHANGELOG.md` when versioning is introduced and GitHub Releases/tags for public release history.
