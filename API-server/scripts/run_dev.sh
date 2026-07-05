#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill SMTP_USER and SMTP_PASS before real email sending."
fi
npm install
npm run dev
