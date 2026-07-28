param(
  [string]$Owner = "takami0928",
  [string]$Repository = "filemaker-server-19.5-script-toolkit"
)

$ErrorActionPreference = "Stop"
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI (gh) is required. Install it, then run gh auth login."
}

gh auth status
if (-not (Test-Path .git)) { git init -b main }
git add .
git commit -m "Initialize FileMaker Server 19.5 script toolkit"
gh repo create "$Owner/$Repository" --public --source . --remote origin --push --description "FileMaker Server 19.5 script standards, fmxmlsnippet validation, and Windows clipboard tooling"
