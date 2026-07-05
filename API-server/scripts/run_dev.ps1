cd $PSScriptRoot\..
if (-Not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "Created .env from .env.example. Please fill SMTP_USER and SMTP_PASS before real email sending."
}
npm install
npm run dev
