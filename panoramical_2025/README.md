# My Hugo Site

# PANORAMICAL Website

A site for PANORAMICAL

---

# Building 

## 🚀 Install Hugo

### macOS (Homebrew)

```bash
brew install hugo
```

### Windows (Scoop / Chocolatey)

```powershell
# Scoop
scoop install hugo

# Chocolatey
choco install hugo -confirm
```

### Linux (APT / Snap)

```bash
# Ubuntu / Debian
sudo apt install hugo

# Snap
sudo snap install hugo --channel=extended
```

Check installation:

```bash
hugo version
```

---

## 🏃 Run locally

1. Clone this repository:

```bash
git clone https://github.com/fernantastic/panoramical-website.git
cd panoramical-website
```

2. Start Hugo server (includes drafts):

```bash
hugo server -D
```

3. Open your browser at:

```
http://localhost:1313/
```

---

## 🏗️ Build for production

```bash
hugo
```

This generates a static website in the `public/` folder.

---

## 🎨 Customize

* Theme: `themes/archie/`
* Content: `content/`
* Layouts & templates: `layouts/`
* Static assets: `static/`
* Config: `hugo.toml`

---