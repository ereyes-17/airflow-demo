#!/usr/bin/env bash
# Set GitHub Actions secrets/variables for this repo from .env
# Requires: gh CLI installed and authenticated (`gh auth login`)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

if ! command -v gh &>/dev/null; then
  echo "ERROR: GitHub CLI (gh) is not installed." >&2
  echo "Install it with one of:" >&2
  echo "  sudo apt install gh" >&2
  echo "  sudo snap install gh" >&2
  echo "Then run: gh auth login" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: .env file not found at ${ENV_FILE}" >&2
  exit 1
fi

# Load .env, stripping surrounding whitespace/quotes and handling CRLF
while IFS='=' read -r key value || [[ -n "${key}" ]]; do
  # strip CR (Windows line endings)
  key="${key%$'\r'}"
  value="${value%$'\r'}"

  # trim leading/trailing whitespace
  key="${key#"${key%%[![:space:]]*}"}"
  key="${key%"${key##*[![:space:]]}"}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"

  # skip blank/comment lines
  [[ -z "${key}" || "${key}" =~ ^# ]] && continue

  # validate key is a valid shell identifier
  if [[ ! "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "  WARNING: '${key}' is not a valid variable name — skipping"
    continue
  fi

  # remove surrounding quotes
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"

  export "${key}=${value}"
done < "${ENV_FILE}"

# ---------------------------------------------------------------------------
# Secrets (sensitive values)
# ---------------------------------------------------------------------------
SECRETS=(
  API_KEY
  POSTGRES_CONN_PASSWORD
  METADATA_DATABASE_PASSWORD
  CELERY_BACKEND_PASSWORD
  ELT_DATABASE_PASSWORD
  AIRFLOW_WWW_USER_PASSWORD
  FERNET_KEY
)

# ---------------------------------------------------------------------------
# Variables (non-sensitive values)
# ---------------------------------------------------------------------------
VARS=(
  CHANNEL_HANDLE
  DOCKERHUB_NAMESPACE
  DOCKERHUB_REPOSITORY
  IMAGE_TAG
  POSTGRES_CONN_USERNAME
  POSTGRES_CONN_HOST
  POSTGRES_CONN_PORT
  METADATA_DATABASE_NAME
  METADATA_DATABASE_USERNAME
  CELERY_BACKEND_NAME
  CELERY_BACKEND_USERNAME
  ELT_DATABASE_NAME
  ELT_DATABASE_USERNAME
  AIRFLOW_UID
  AIRFLOW_WWW_USER_USERNAME
)

echo "Creating/updating GitHub Secrets ..."
for secret in "${SECRETS[@]}"; do
  value="${!secret:-}"
  if [[ -z "${value}" ]]; then
    echo "  WARNING: ${secret} is empty or missing in .env — skipping"
    continue
  fi
  printf '%s' "${value}" | gh secret set "${secret}"
  echo "  ✓ ${secret}"
done

echo "Creating/updating GitHub Variables ..."
for var in "${VARS[@]}"; do
  value="${!var:-}"
  if [[ -z "${value}" ]]; then
    echo "  WARNING: ${var} is empty or missing in .env — skipping"
    continue
  fi
  gh variable set "${var}" --body "${value}"
  echo "  ✓ ${var}"
done

echo ""
echo "Done."
echo ""
echo "NOTE: Your workflow also references these items that are NOT in .env:"
echo "  Secret:  DOCKERHUB_PASSWORD     (used in build-and-push-image job)"
echo "  Variable: DOCKERHUB_USERNAME     (used in build-and-push-image job)"
echo "Add them manually if they don't already exist:"
echo "  gh secret set DOCKERHUB_PASSWORD"
echo "  gh variable set DOCKERHUB_USERNAME --body 'your-dockerhub-username'"
