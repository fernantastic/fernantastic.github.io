+++
draft = false
title = "Rest of Us - A Collaborative Shader Sketchbook"
home_img = "projects/shaderclass/shader-gallery.jpg"
home_title = "Rest of Us - Collaborative Shader Sketchbook"
home_subtitle = "Creative Tools, Graphics Programming, Teaching"
side = """
Roles:
Creative Tool Development
Graphics Programming
Interface Design
Teaching

Tools:
GLSL / WebGL2
TypeScript / Vite
Monaco Editor
Yjs / WebSockets
Cloudflare Pages
D1 / Durable Objects / R2
"""
description = """
I made a live shader sketchbook for visual artists: **edit code, play with the image, and make something together in the browser.**

Built for my class **Shaders Demystified: Graphics code as material for visual artists** at the [School for Poetic Computation](https://sfpc.study), Fall 2026.

It started as a tool for my shader experiments and grew into a classroom app with student galleries, multiplayer editing and publishing tools.

Features:

* Live GLSL editing and WebGL2 preview
* Sliders, colors and texture controls generated from shader code
* Mouse interaction and live webcam textures
* Categorized teaching examples and student galleries
* Forking with source credits and ancestry
* Multiplayer code editing, shared controls and participant presence
* Cloud saves, visual revision history and restore
* Class sharing, edit permissions and revocable public links
* Adjustable resolution, aspect ratios and kiosk display
* Image, GIF and video capture
* Sketch and gallery exports with source files and HTML players
* R2 texture library with optimized image formats
* Account, class and category administration

Built with TypeScript, WebGL2 and Monaco, using Yjs for collaboration. Hosted on Cloudflare Pages with D1, Durable Objects and R2.
"""
+++

{{< img "projects/shaderclass/shader-gallery.jpg" "The shader browser." >}}

I enjoy making creative tools where you can quickly try an idea and see what happens. For this class I wanted students to open a shader they liked, change a few things, and start finding their own images in it.

I built the editor, rendering tools and example library, then added the online features for saving work and using it together in class.

## Live shader editing

GLSL code on one side, the image on the other. Students can recompile as they type or compile manually, then play with values through sliders and color pickers. The examples start with simple shapes and patterns, using coordinates, distance and time to build an image pixel by pixel.

{{< loopvideo "rings" "An animated study in distance and repetition, with its code and controls alongside it." >}}

The controls are generated from the shader itself. I wrote a parser that reads uniform declarations, with defaults and ranges in comments, and turns them into sliders, vector controls, color pickers and texture selectors. Adding a parameter to the shader also adds it to the interface.

Those values are used by the renderer, saved with the sketch and synchronized in multiplayer rooms. Shaders can also respond to mouse position and dragging, or use a live webcam feed as a texture.

{{< img "projects/shaderclass/ripple-shader.jpg" "Playing with color and concentric ripples." >}}

The editor uses Monaco and a custom WebGL2 renderer. It resolves GLSL includes and maps compiler errors back to the source files. Parallel shader compilation is used where supported, checking for completion across frames. Students can lower the render resolution for heavier shaders, set a fixed pixel size, or choose an aspect ratio for the image.

## Teaching examples and student sketches

I put together a library that moves from basic math and color to noise, signed distance fields, raymarching, landscapes and atmosphere. Students fork an example, assign it to the right week, and change it using the techniques from class.

{{< img "projects/shaderclass/shader-library.jpg" "Examples grouped by technique." >}}

The browser has sections for personal sketches, the class showcase, teacher examples, recent work and collaborative shaders. Each sketch has a thumbnail, author, notes and category. Forks keep their source credits and ancestry, so students can follow how an example turned into someone else's experiment.

{{< loopvideo "sphere" "Repeated forms in a 3D shader, live in the editor." >}}

I added account and admin tools for running the class: creating users, assigning sections, organizing categories and choosing who can edit a sketch. Students can manage their work and share it with the class through the same interface.

## Multiplayer shader editing

**Party Shaders** are shared sketches that students can edit together in realtime. Open your party shader, send its address to a classmate, and both of you can change the code and controls. Names, colored editor selections and highlights on active controls show what the other person is doing.

I used **Yjs** to merge simultaneous code edits, with `y-monaco` connecting the shared text to the editor. Uniforms, controls and sketch settings use shared maps. Presence messages carry participant names and interaction indicators separately from the saved shader.

Each room runs in a **Cloudflare Durable Object**, connected through an authenticated WebSocket endpoint. It handles document synchronization and broadcasts changes to everyone in the room. The server supplies the user's identity for presence messages and removes their indicators when they disconnect. The room's document is persisted so it can be reopened later.

## Saving and returning to an experiment

Sketches have a visual revision history with thumbnails, dates and authors. Students can open an earlier version, restore it, or fork it into a new sketch. Browser drafts also preserve work during editing.

{{< loopvideo "palette" "A palette cycling pattern, live in the editor." >}}

I keep the working revision separate from the last saved version in the database. That lets collaborative recovery snapshots preserve unfinished edits while public links show the saved sketch. The history records saves, restores, forks and collaboration snapshots, along with their source revisions.

For multiplayer, the Durable Object batches frequent changes before persisting the Yjs document. Scheduled alarms write recovery snapshots to D1 when the shader or settings have changed, using a content hash to avoid duplicates. Old autosaves are pruned, and another snapshot is scheduled when the last person leaves. Manual saves create checkpoints in the same revision history.

## Sharing, capture and export

Students can make a public link for someone outside the class to see their shader and its code. These links are read-only and can be revoked. Kiosk mode hides the interface for displaying a piece or using it as a browser source in OBS.

The capture tools export images, GIFs and video at different sizes and aspect ratios. Procedural animations are rendered frame by frame at defined times, so a heavy shader can be recorded even when it runs slowly in the editor.

ZIP exports include the GLSL, settings, thumbnail and an HTML player. The player expands shared shader includes and restores numeric uniforms for sketches it supports. Students can also export their whole library with a gallery page, keeping the source files available to use elsewhere.

## Cloud hosting and storage

The app runs on Cloudflare, with different services handling the web interface, saved work and live collaboration:

| Service | Used for |
| --- | --- |
| Pages and Pages Functions | Frontend and API for accounts, sketches and sharing |
| D1 | Accounts, class data, sketches, thumbnails, revisions and fork ancestry |
| Durable Objects | Live rooms, WebSocket connections and recovery state |
| R2 | The texture library |

I designed the D1 schema around sketches and their history. Each sketch references its owner and revisions; each revision stores GLSL and serialized settings. A separate table tracks fork ancestry. The API handles password hashing, expiring sessions, login rate limits and ownership checks for editing and management. Database migrations and an SQL backup workflow support ongoing changes to the app.

Textures are hosted in **R2** and selected through asset manifests. These keep track of dimensions, color space, tiling, credits, licenses and available formats. The loader resolves a texture name to an R2 file, preferring available AVIF or WebP versions, with PNG options and a separate path for precise source images. Sketches keep the same texture names when delivery formats change.

The shared library and course assets have separate manifests, so I can add textures for a project without changing the common collection.

## Reusable graphics tools

The app is built on my TypeScript **ShaderLibrary**, which contains the renderer, editor, parameter controls and capture tools. I wrote a Vite plugin to discover sketches and generate their loaders, shader sources, includes and thumbnail references. Locally, it also handles shader hot reload and saving code and settings back to files. Online student sketches load their GLSL and settings from D1 through a common wrapper.

The library also includes multiple rendering passes, Three.js scenes and particles, audio playback, a separate WebGPU path, named variations and keyframe timelines. The classroom version hides the advanced pass, variation and timeline controls to keep the interface simple. I can use those tools in other projects built on the same library.

{{< img "projects/shaderclass/help-panel.jpg" "Built-in help, shader references and links." >}}

## Shaders Demystified

The class is for visual artists who already use code and want to explore shaders, but feel intimidated by the math. We take apart existing work, change it, and build up a collection of techniques for making our own images.

Alongside GLSL, we look at the demoscene and the communities where these techniques developed. The final assignment is to modify a shader to express a thought, moment or feeling. I wanted the tool to support that kind of curious, personal experimentation.

**Shaders Demystified: Graphics code as material for visual artists**  
Teacher: [Fernando Ramallo](https://byfernando.com/)  
TA: Jonathan Brodsky  
School for Poetic Computation, Fall 2026
