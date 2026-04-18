#!/usr/bin/env bash
# =============================================================================
# Setup Google Secret Manager secrets for Creative Reviewer
# =============================================================================
# Usage:
#   1. Edit the .env file with your production values
#   2. Run: bash scripts/setup_secrets.sh
#
# This script reads secret names from .env.example and creates them in
# Google Secret Manager. You must have the Secret Manager Admin IAM role.
# =============================================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-abcds-detector-488021}"

echo "==> Creating secrets in project: ${PROJECT_ID}"

# List of secrets to create (must match .env variable names)
SECRETS=(
  "SESSION_SECRET"
  "GOOGLE_CLIENT_ID"
  "GOOGLE_CLIENT_SECRET"
  "STRIPE_SECRET_KEY"
  "STRIPE_WEBHOOK_SECRET"
  "STRIPE_PRICE_1000"
  "STRIPE_PRICE_3000"
  "DATABASE_URL"
  "ABCD_KG_API_KEY"
  "SLACK_WEBHOOK_URL"
  "SMTP_HOST"
  "SMTP_USER"
  "SMTP_PASSWORD"
)

for SECRET_NAME in "${SECRETS[@]}"; do
  # Check if secret already exists
  if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  [exists] ${SECRET_NAME}"
  else
    echo "  [create] ${SECRET_NAME}"
    gcloud secrets create "${SECRET_NAME}" \
      --project="${PROJECT_ID}" \
      --replication-policy="automatic"
  fi
done

echo ""
echo "==> Secrets created. To set values:"
echo ""
echo "  echo -n 'YOUR_VALUE' | gcloud secrets versions add SECRET_NAME --data-file=- --project=${PROJECT_ID}"
echo ""
echo "==> To reference in Cloud Run deploy:"
echo ""
echo "  gcloud run deploy creative-reviewer \\"
echo "    --set-secrets=SESSION_SECRET=SESSION_SECRET:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,... \\"
echo "    --project=${PROJECT_ID}"
echo ""
echo "Done."
