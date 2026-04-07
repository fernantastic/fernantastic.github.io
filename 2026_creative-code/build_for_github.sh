#!/usr/bin/env bash

set -euo pipefail

hugo build --gc --minify --baseURL "https://byfernando.com/2026/"
