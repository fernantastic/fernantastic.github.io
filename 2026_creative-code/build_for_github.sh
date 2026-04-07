#!/usr/bin/env bash

set -euo pipefail

hugo build --gc --minify --config "hugo.toml,hugo.github.toml"
