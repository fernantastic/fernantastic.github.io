+++
draft = false
title = "Complete Live Code Sketchbook Platform for Students"
home_img = "projects/shaderclass/shader-gallery.jpg"
home_title = "Shaders Demystified"
home_subtitle = "Shader Art, GLSL, Creative Coding"
side = """
Roles:
Teaching
Creative Coding

Tools:
TypeScript
WebGL2
Vite
Yjs
Cloudflare Pages
Cloudflare D1
Durable Objects
Cloudflare R2
"""
description = """
A live visual coding sketchbook that grew into a full collaborative publishing and classroom platform. 

Made for my class **Shaders Demystified: Graphics code as material for visual artists** at the [School for Poetic Computation](http://sfpc.study), taught in the Fall of 2026.

Built with TypeScript and WebGL2, hosted on Cloudflare Pages, uses D1, Durable Objects, R2. 

Features:
 * Live GLSL editing with WebGL2 preview
 * Categorized shader library and search
 * Fork bundled and student sketches
 * Uniform-driven sliders, colors, and texture controls
 * Interactive pointer, webcam, and audio inputs
 * Sketch metadata, thumbnails, and visibility settings
 * Revision history, restore, and saved checkpoints
 * Multiplayer rooms with shared code, controls, and presence
 * Personal, class, and professor libraries
 * Revocable read-only public links
 * ZIP and standalone HTML exports
 * Still image, GIF, and video capture
 * R2 texture library with optimized image formats
 * Admin tools for accounts, sections, classes, and categories
"""
+++

**Rest of Us** is **a live sketchbook for editing and collaborating on visual code shaders together**. 
{{< img "projects/shaderclass/shader-gallery.jpg" "" >}}


**Technical overview:** TypeScript and Vite frontend; Monaco GLSL editor; WebGL2 renderer; Cloudflare Pages Functions API; D1 accounts, sketches and revision history; Yjs multiplayer over WebSockets, coordinated by per-room Durable Objects; texture manifests pointing to optimized Cloudflare R2 assets.


## Editing a visual sketch live

The code editor and image sit side by side: change a number or reshape a function, and the visual result updates in place. 

The aim is to make shader code feel like something you can handle and play with, even when the math is unfamiliar.
{{< img "projects/shaderclass/target-shader.jpg" "" >}}

## Editing a visual sketch live

{{< img "projects/shaderclass/shader-library.jpg" "" >}}

Students edit GLSL code and see the resulting image change in realtime as they edit the code.

The opening view gathers small studies into a path through **start**, **math**, **2D**, **3D**, **3D SDFs**, **landscape** and **advanced**. That order follows the course: begin with coordinates, color and simple functions, then work toward signed distance fields, raymarching, noise, atmosphere and volumetric effects. The online version extends this teaching library with student and professor collections, saved sketches, class visibility, public links and collaborative rooms.

{{< img "projects/shaderclass/sphere-shader.jpg" "" >}}

Opening a sketch reveals its GLSL beside the live canvas. Repeated spheres turn distance-based geometry into a spatial field. Each sketch is a small TypeScript experiment wrapper and a fragment shader; the wrapper loads the shader and declares its category and metadata, while the GPU evaluates the fragment program for every pixel. Built-in uniforms pass time, resolution, aspect ratio and pointer state into the render loop.

{{< img "projects/shaderclass/ripple-shader.jpg" "" >}}

A ripple study makes a direct connection between a formula and its visual rhythm. Uniform declarations can include default values and numeric ranges in comments. A parser reads them to build the tweak panel, so students can change the same shader parameters either in the source or through controls and immediately compare the results.


A target pattern shows how a compact analytical shape can become a graphic language. Signed distance values can become edges, outlines, glows or palettes depending on how they are remapped. These studies make useful teaching examples because the visual result is striking while the underlying rule stays small enough to inspect and alter.


The library is also an archive of work in progress. Sketch cards carry titles, notes, categories, ownership, visibility, thumbnails and links back through their fork history. Students can start a sketch, fork a bundled or online example, save a new version, revisit an earlier revision, or publish a read-only link. The browse views separate personal work, class work, professor examples and party shaders while keeping the image preview central.

## From sketchbook to hosted app

The project has two related layers. The local `restofus-tool` repository is the teaching editor and its reusable ShaderLibrary. The hosted classroom app lives in `web-version/restofus-tool-online`; it reuses that shader foundation and adds accounts, database-backed sketch collections, public publishing and multiplayer. The page and screenshots here show the sketch-editor lineage; the sections below describe the complete online system.

The frontend is TypeScript and Vite. The host mounts the ShaderLibrary Web Component, which owns the canvas, sketch browser, Monaco code panel, tweak controls, timeline and capture tools. A Vite plugin generates a virtual host-project module because a library package cannot use `import.meta.glob` to reach into the consuming app's source tree. That generated module indexes experiment classes, raw GLSL sources, includes, thumbnails and tweak presets. In the online build, professor examples are bundled from the repository, while student sketches are loaded as data from D1 rather than executed as arbitrary TypeScript.

The renderer uses WebGL2. It preprocesses shader includes, compiles and links GLSL programs, maps compiler errors back through the include/source line map, and swaps in successful recompiles without rebuilding the whole page. The frame loop updates built-in uniforms and applies the current tweak group. Pointer position, buttons and drag are available as shader inputs; the library also includes webcam and audio input paths. Optional extensions add Three.js rendering passes, particles, texture inputs and multipass effects, with a separate WebGPU experiment path where a sketch needs more than a single fragment shader.

The editor is Monaco-based, loaded from its smaller editor API entry rather than the full bundle. It supports multiple shader files and GLSL language services; a scrubber widget can connect editable source values to tweak controls and keyframe them. Draft buffers survive page reloads in session storage. In the local development build, Vite middleware reads and writes source files, persists tweak JSON and forks sketch directories, while the Vite watcher pushes shader edits into the running canvas. In the hosted build, edits are saved as database revisions instead of writing to the deployed filesystem.

## Parameters, variations and motion

A uniform parser turns GLSL declarations into a typed tweak schema. Floats and integers become sliders or numeric inputs; vectors become component controls; color vectors become color pickers; sampler uniforms become texture pickers. Comment annotations provide defaults, ranges and folder grouping without maintaining a second control schema by hand. The tweak group acts as the shared state source for the UI, renderer, saved sketch state and collaboration bindings.

The shared shader library also contains named variations and snapshot timelines: looks can be saved separately from the shader source, and keyframes, easing, sections and layered timelines can animate parameter values. These controls are feature-gated, though. In the hosted classroom configuration, timeline authoring and the variations panel are disabled; the app relies on explicit saves, revision history and collaborative room autosnapshots instead. The capture system remains available for stills, GIFs and video at chosen sizes and aspect ratios, with deterministic timeline seeking available in builds that enable timeline controls. Thumbnails give saved sketches and revisions a visual index.

{{< img "projects/shaderclass/contour-shader.jpg" "" >}}

The contour sketch illustrates how one scalar field can drive a complete image. The tool's parameter layer keeps that relationship inspectable: a student can tune a value, record it in a variation or timeline, then trace it back to the uniform and the GLSL function that consumes it.

## Students can collaborate by editing shaders together in realtime

The online app gives each collaborative sketch a persistent room. A signed-in student or professor opens a room from the app; the Pages Function checks the user's access against the sketch and room records, then routes the WebSocket upgrade to the Durable Object named for that room. Each room has one `MultiuserRoom` object, which gives its live state a single coordination point.

Inside the Durable Object, a Yjs document stores the shader as collaborative text and room settings as shared maps. The browser binds that shared text directly to Monaco through `y-monaco`, so concurrent edits merge as document updates instead of replacing the whole shader buffer. Uniforms and editor controls are also synchronized as shared values. Yjs awareness carries ephemeral presence: participant names and stable colors, plus a pointer highlight while someone is interacting with a control. Presence is broadcast to peers but is not written into the sketch's saved content.

The room worker speaks the Yjs sync and awareness protocols over WebSockets. It tags each socket with the authenticated user's identity, adds trusted identity data to awareness updates, broadcasts document changes to other connected clients, and removes a participant's awareness state when their socket closes. It rejects malformed or oversized messages and checks room access before the connection is handed to the Durable Object.

{{< img "projects/shaderclass/help-panel.jpg" "" >}}

The help panel keeps references close to the creative workspace. In the online app, the same idea extends to shared activity: people in a room can see who is present and which control another person is exploring, making a remote classroom feel more like looking at the same desk together.

## Persistence, revisions and recovery

Cloudflare Pages Functions provide the authenticated JSON API for the app. Cloudflare D1 stores users, sessions, sections, sketches, room membership, categories, revision metadata and the shader/tweak payloads associated with each revision. Sketch records hold ownership, class or section placement, visibility, draft state, metadata, thumbnail data and pointers to their current and last explicitly saved revisions. Foreign keys and indexes support owner, section, visibility, room and revision-history queries.

Every meaningful save creates a revision with its kind, action, author, timestamp, source revision and trigger. The model distinguishes a current working revision from the last manually saved revision: autosaves can protect ongoing work without silently publishing it as the saved checkpoint. Restore and fork operations retain source-revision links, and a provenance table records ancestry across both online sketches and bundled course examples. Thumbnail endpoints store previews for sketches and individual revisions, so browsing history remains visual.

The Durable Object keeps the active Yjs document in its own persistent SQLite-backed storage and batches frequent edits before persisting the encoded document state. A scheduled alarm periodically compares a content hash of the collaborative shader and tweak state with the latest D1 revision; if changed, it writes an autosave revision and prunes older periodic autosaves beyond the configured history limit. A manual room snapshot creates a durable checkpoint and advances both the current and saved revision pointers. When the last participant leaves, dirty room state is persisted and an alarm is scheduled so work can still be snapshotted after disconnection.

D1 is the durable product record and revision history; the Durable Object is the live collaboration coordinator and recovery buffer. A separate backup workflow exports the database daily, alongside Cloudflare D1 Time Travel for point-in-time recovery. The API creates, lists, updates, forks, restores and deletes sketches; controls visibility and public links; serves thumbnails and revisions; and exposes room, profile, class and administration operations. Authentication uses password hashes and expiring server-side sessions, with rate-limited login attempts and role-aware authorization for student and admin actions. Students can update their display name and browse personal, class and professor libraries; the API enforces sketch ownership, visibility and editability for read, write, fork, restore and delete operations. Public links provide read-only access to a selected sketch and can be revoked by its owner. Administrators can manage users, sections, categories, category order and class groupings through the same API.

## Texture delivery and export

Textures are resolved through manifests rather than copied into every sketch. The shared ShaderLibrary manifest records asset keys, source properties, licensing and available image variants, together with a Cloudflare R2 public base URL. The resolver selects an AVIF or WebP variant when available and falls back to PNG, then combines the relative object path with the base URL. Shaders keep stable logical texture keys while the browser downloads optimized files directly from R2. A separate Rest of Us manifest allows project-specific assets without mixing them into the shared library.

The hosted browser also supports exporting one sketch or a whole gallery. ZIP exports package the shader files, tweak settings and thumbnails; standalone HTML exports inline the shared GLSL includes, compile a WebGL2 program in the browser and restore the saved uniforms. That makes an individual sketch playable without the editor, while gallery exports provide a small navigable portfolio. This connects a hosted database workflow back to files that can be inspected, shared or carried into another creative coding setup.

### Class

**Shaders Demystified: Graphics code as material for visual artists**  
Teacher: [Fernando Ramallo](https://byfernando.com/)  
TA: Jonathan Brodsky






