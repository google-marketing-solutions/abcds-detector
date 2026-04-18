#!/usr/bin/env bash
# =============================================================================
# Deploy Creative Reviewer to Google Cloud Run
# =============================================================================
# Usage:
#   bash scripts/deploy.sh
#
# Prerequisites:
#   1. gcloud CLI authenticated: gcloud auth login
#   2. Secrets created in Secret Manager: bash scripts/setup_secrets.sh
#   3. Artifact Registry repo created (one-time):
#      gcloud artifacts repositories create creative-reviewer \
#        --repository-format=docker --location=us-central1
# =============================================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-abcds-detector-488021}"
REGION="us-central1"
SERVICE_NAME="abcds-detector"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/creative-reviewer/app"
TAG="$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"

echo "==> Building Docker image: ${IMAGE}:${TAG}"
docker build \
  --platform linux/amd64 \
  --tag "${IMAGE}:${TAG}" \
  --tag "${IMAGE}:latest" \
  .

echo "==> Pushing to Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
docker push "${IMAGE}:${TAG}"
docker push "${IMAGE}:latest"

echo "==> Deploying to Cloud Run: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}:${TAG}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --platform managed \
  --cpu 4 \
  --memory 4Gi \
  --concurrency 4 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars "\
ENVIRONMENT=production,\
PUBLIC_BASE_URL=https://app.aicreativereview.com,\
ALLOWED_ORIGINS=https://app.aicreativereview.com" \
  --set-secrets "\
SESSION_SECRET=SESSION_SECRET:latest,\
GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,\
GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,\
STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest,\
STRIPE_WEBHOOK_SECRET=STRIPE_WEBHOOK_SECRET:latest,\
STRIPE_PRICE_1000=STRIPE_PRICE_1000:latest,\
STRIPE_PRICE_3000=STRIPE_PRICE_3000:latest,\
DATABASE_URL=DATABASE_URL:latest,\
ABCD_KG_API_KEY=ABCD_KG_API_KEY:latest,\
SLACK_WEBHOOK_URL=SLACK_WEBHOOK_URL:latest" \
  --set-cloudsql-instances "${PROJECT_ID}:${REGION}:creative-reviewer-db" \
  --vpc-connector cr-vpc-connector \
  --vpc-egress private-ranges-only \
  --service-account "abcds-detector-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --quiet

echo ""
echo "==> Deployment complete!"
gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format 'value(status.url)'
