# Tiny Walk Website

This folder is already a Hugo site. It now includes a small `.vscode/` setup so it opens cleanly in VS Code and gives you one-click local preview/build tasks.

## VS Code

Open this folder directly in VS Code:

```bash
code /Users/fernantastic/src/_synced/website_pano/fernantastic.github.io/2026_creative-code
```

Recommended workflow inside VS Code:

1. Install the recommended extensions when VS Code prompts you.
2. Run `Tasks: Run Task` and choose `Hugo: dev server`.
3. Open `http://localhost:1313`.

On macOS, you can also press `F5` and launch `Open Hugo site` after the dev server is already running. That uses the system default browser.

## Hugo

Install Hugo extended if needed:

```bash
brew install hugo
hugo version
```

Run locally:

```bash
hugo server -D --disableFastRender
```

Build production output:

```bash
hugo --gc --minify
```

Generated output goes to `public/`.

## Project Structure

- `content/` page content
- `layouts/` custom templates and partials
- `assets/` processed assets
- `static/` files copied as-is
- `themes/` installed themes
- `hugo.toml` site configuration
