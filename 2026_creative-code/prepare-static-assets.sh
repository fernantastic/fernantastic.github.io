#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DIR="${ROOT_DIR}/assets/raw-static-assets"
STATIC_DIR="${ROOT_DIR}/static"
MAX_BYTES=$((500 * 1024))
MAX_WIDTH=1920
MAX_HEIGHT=1080
OGV_MAX_WIDTH=960
WEBP_MAX_WIDTH=500
WEBP_FPS=12
WEBP_QUALITY=82

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick ('magick') is required." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required." >&2
  exit 1
fi

if ! command -v webpinfo >/dev/null 2>&1; then
  echo "webpinfo is required." >&2
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

video_dimensions() {
  ffmpeg -i "$1" 2>&1 | sed -nE 's/.* ([0-9]+)x([0-9]+)[, ].*/\1 \2/p' | head -n 1
}

webp_dimensions() {
  webpinfo "$1" 2>/dev/null | sed -nE 's/.*Canvas size:? ([0-9]+) x ([0-9]+).*/\1 \2/p' | head -n 1
}

even_round() {
  local value="$1"
  local rounded=$(( (value + 1) / 2 * 2 ))
  printf '%s\n' "${rounded}"
}

expected_webp_dimensions() {
  local src="$1"
  local src_width src_height target_width target_height
  read -r src_width src_height <<<"$(video_dimensions "$src")"
  if (( src_width <= WEBP_MAX_WIDTH )); then
    target_width="${src_width}"
    target_height="$(even_round "${src_height}")"
  else
    target_width="${WEBP_MAX_WIDTH}"
    target_height="$(even_round $(( src_height * target_width / src_width )))"
  fi
  printf '%s %s\n' "${target_width}" "${target_height}"
}

webp_matches_expected_dimensions() {
  local src="$1"
  local dest="$2"
  local expected_width expected_height actual_width actual_height
  [[ -f "${dest}" ]] || return 1
  read -r expected_width expected_height <<<"$(expected_webp_dimensions "${src}")"
  read -r actual_width actual_height <<<"$(webp_dimensions "${dest}")"
  [[ "${actual_width}" == "${expected_width}" && "${actual_height}" == "${expected_height}" ]]
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

convert_video_to_webm() {
  local src="$1"
  local dest="$2"
  ensure_parent_dir "${dest}"
  if is_up_to_date "${src}" "${dest}"; then
    log "skip webm ${dest#${ROOT_DIR}/}"
    return
  fi

  ffmpeg -y -i "${src}" \
    -vf "scale='min(${MAX_WIDTH},iw)':-2:force_original_aspect_ratio=decrease" \
    -c:v libvpx-vp9 -pix_fmt yuv420p -row-mt 1 -b:v 0 -crf 33 \
    -an \
    "${dest}" \
    >/dev/null 2>&1
  log "convert webm ${dest#${ROOT_DIR}/}"
}

convert_video_to_ogv() {
  local src="$1"
  local dest="$2"
  local tmp_dest
  ensure_parent_dir "${dest}"
  if is_up_to_date "${src}" "${dest}"; then
    log "skip ogv ${dest#${ROOT_DIR}/}"
    return
  fi

  tmp_dest="${dest}.tmp.ogv"
  rm -f "${tmp_dest}"

  ffmpeg -y -i "${src}" \
    -vf "scale='min(${OGV_MAX_WIDTH},iw)':-2:force_original_aspect_ratio=decrease" \
    -c:v libtheora -q:v 5 \
    -an \
    "${tmp_dest}" \
    >/dev/null 2>&1
  mv "${tmp_dest}" "${dest}"
  log "convert ogv ${dest#${ROOT_DIR}/}"
}

convert_video_to_webp() {
  local src="$1"
  local dest="$2"
  local tmp_dest
  ensure_parent_dir "${dest}"
  if is_up_to_date "${src}" "${dest}" && webp_matches_expected_dimensions "${src}" "${dest}"; then
    log "skip webp ${dest#${ROOT_DIR}/}"
    return
  fi

  tmp_dest="${dest}.tmp.webp"
  rm -f "${tmp_dest}"

  ffmpeg -y -i "${src}" \
    -vf "fps=${WEBP_FPS},scale='min(${WEBP_MAX_WIDTH},iw)':-2:force_original_aspect_ratio=decrease:flags=lanczos" \
    -quality 90 \
    -compression_level 4 \
    -q:v "${WEBP_QUALITY}" \
    -loop 0 \
    -an \
    "${tmp_dest}" \
    >/dev/null 2>&1
  mv "${tmp_dest}" "${dest}"
  log "convert webp ${dest#${ROOT_DIR}/}"
}

process_file() {
  local src="$1"
  local rel="${src#${RAW_DIR}/}"
  local ext lower_ext size dest base
  if [[ ! -f "${src}" ]]; then
    log "skip missing ${src}"
    return
  fi
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
      convert_video_to_webm "${src}" "${STATIC_DIR}/${base}.webm"
      convert_video_to_ogv "${src}" "${STATIC_DIR}/${base}.ogv"
      convert_video_to_webp "${src}" "${STATIC_DIR}/${base}.webp"
      ;;
    *)
      log "skip unsupported ${rel}"
      ;;
  esac
}

export ROOT_DIR RAW_DIR STATIC_DIR MAX_BYTES MAX_WIDTH MAX_HEIGHT OGV_MAX_WIDTH WEBP_MAX_WIDTH WEBP_FPS WEBP_QUALITY
export -f log ensure_parent_dir is_up_to_date image_dimensions video_dimensions webp_dimensions even_round expected_webp_dimensions webp_matches_expected_dimensions resize_geometry_for_image copy_asset convert_image_to_jpeg convert_video_to_mp4 convert_video_to_webm convert_video_to_ogv convert_video_to_webp process_file

process_targets() {
  if (( $# == 0 )); then
    find "${RAW_DIR}" -type f ! -name '.DS_Store' -print0 | while IFS= read -r -d '' file; do
      process_file "${file}"
    done
    return
  fi

  local target
  local abs_target
  for target in "$@"; do
    if [[ -d "${target}" ]]; then
      abs_target="$(cd "${target}" && pwd)"
      find "${abs_target}" -type f ! -name '.DS_Store' -print0 | while IFS= read -r -d '' file; do
        process_file "${file}"
      done
    elif [[ -f "${target}" ]]; then
      abs_target="$(cd "$(dirname "${target}")" && pwd)/$(basename "${target}")"
      process_file "${abs_target}"
    else
      log "skip missing ${target}"
    fi
  done
}

process_targets "$@"
