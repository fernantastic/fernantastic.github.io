#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DIR="${ROOT_DIR}/assets/raw-static-assets"
STATIC_DIR="${ROOT_DIR}/static"
MAX_BYTES=$((500 * 1024))
MAX_WIDTH=1920
MAX_HEIGHT=1080

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick ('magick') is required." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required." >&2
  exit 1
fi

if [[ ! -d "${RAW_DIR}" ]]; then
  exit 0
fi

log() {
  printf '%s\n' "$*"
}

ensure_parent_dir() {
  mkdir -p "$(dirname "$1")"
}

is_up_to_date() {
  local src="$1"
  local dest="$2"
  [[ -f "${dest}" && "${dest}" -nt "${src}" ]]
}

image_dimensions() {
  magick identify -format '%w %h' "${1}[0]" | head -n 1
}

resize_geometry_for_image() {
  local src="$1"
  local width height
  read -r width height <<<"$(image_dimensions "$src")"
  if (( width > MAX_WIDTH || height > MAX_HEIGHT )); then
    printf '%s' "${MAX_WIDTH}x>"
  else
    printf '%s' ""
  fi
}

copy_asset() {
  local src="$1"
  local dest="$2"
  ensure_parent_dir "${dest}"
  if is_up_to_date "${src}" "${dest}"; then
    log "skip copy ${dest#${ROOT_DIR}/}"
    return
  fi
  cp "${src}" "${dest}"
  log "copy ${dest#${ROOT_DIR}/}"
}

convert_image_to_jpeg() {
  local src="$1"
  local dest="$2"
  local resize_arg
  resize_arg="$(resize_geometry_for_image "${src}")"
  ensure_parent_dir "${dest}"
  if is_up_to_date "${src}" "${dest}"; then
    log "skip image ${dest#${ROOT_DIR}/}"
    return
  fi

  rm -f "${dest%.*}"-*.jpg

  if [[ -n "${resize_arg}" ]]; then
    magick "${src}[0]" -auto-orient -resize "${resize_arg}" -strip -quality 100 "${dest}"
  else
    magick "${src}[0]" -auto-orient -strip -quality 100 "${dest}"
  fi
  log "convert image ${dest#${ROOT_DIR}/}"
}

convert_video_to_mp4() {
  local src="$1"
  local dest="$2"
  ensure_parent_dir "${dest}"
  if is_up_to_date "${src}" "${dest}"; then
    log "skip video ${dest#${ROOT_DIR}/}"
    return
  fi

  ffmpeg -y -i "${src}" \
    -vf "scale='min(${MAX_WIDTH},iw)':-2:force_original_aspect_ratio=decrease" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -preset medium -crf 21 \
    -movflags +faststart \
    -an \
    "${dest}" \
    >/dev/null 2>&1
  log "convert video ${dest#${ROOT_DIR}/}"
}

process_file() {
  local src="$1"
  local rel="${src#${RAW_DIR}/}"
  local ext lower_ext size dest base
  ext="${src##*.}"
  lower_ext="$(printf '%s' "${ext}" | tr '[:upper:]' '[:lower:]')"
  size="$(stat -f '%z' "${src}")"
  base="${rel%.*}"

  case "${lower_ext}" in
    gif)
      dest="${STATIC_DIR}/${rel}"
      copy_asset "${src}" "${dest}"
      ;;
    jpg|jpeg)
      dest="${STATIC_DIR}/${rel}"
      if (( size <= MAX_BYTES )); then
        copy_asset "${src}" "${dest}"
      else
        convert_image_to_jpeg "${src}" "${STATIC_DIR}/${base}.jpg"
      fi
      ;;
    png)
      if (( size <= MAX_BYTES )); then
        dest="${STATIC_DIR}/${rel}"
        copy_asset "${src}" "${dest}"
      else
        convert_image_to_jpeg "${src}" "${STATIC_DIR}/${base}.jpg"
      fi
      ;;
    webp)
      dest="${STATIC_DIR}/${rel}"
      copy_asset "${src}" "${dest}"
      ;;
    mp4)
      convert_video_to_mp4 "${src}" "${STATIC_DIR}/${base}.mp4"
      ;;
    *)
      log "skip unsupported ${rel}"
      ;;
  esac
}

export ROOT_DIR RAW_DIR STATIC_DIR MAX_BYTES MAX_WIDTH MAX_HEIGHT
export -f log ensure_parent_dir is_up_to_date image_dimensions resize_geometry_for_image copy_asset convert_image_to_jpeg convert_video_to_mp4 process_file

find "${RAW_DIR}" -type f ! -name '.DS_Store' | while read -r file; do
  process_file "${file}"
done
