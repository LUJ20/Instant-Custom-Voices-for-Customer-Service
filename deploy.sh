#!/usr/bin/env bash
# Copyright 2026 Google LLC
# Author: Layolin Jesudhass <layolin@google.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo '')}}}"
REGION="${2:-${GOOGLE_CLOUD_LOCATION:-${GCP_REGION:-$(gcloud config get-value run/region 2>/dev/null || echo 'us-central1')}}}"
BUCKET_NAME="${3:-${GCS_BUCKET_NAME:-${PROJECT_ID}-cust-service-voice}}"
ACCOUNT="${4:-${GCP_AUTH_ACCOUNT:-$(gcloud config get-value account 2>/dev/null || echo '')}}"
SERVICE_NAME="instant-custom-voice-cust-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
    echo "ERROR: Please specify a project ID as an argument or set GOOGLE_CLOUD_PROJECT."
    echo "Usage: ./deploy.sh [PROJECT_ID] [REGION] [BUCKET_NAME] [ACCOUNT]"
    exit 1
fi

ACCOUNT_FLAG=()
if [ -n "${ACCOUNT}" ] && [ "${ACCOUNT}" != "(unset)" ]; then
    ACCOUNT_FLAG=("--account=${ACCOUNT}")
fi

echo "=========================================================="
echo " Deploying Instant Custom Voice Customer Service Demo"
echo " Project: ${PROJECT_ID}"
echo " Region:  ${REGION}"
echo " Service: ${SERVICE_NAME}"
echo " Bucket:  ${BUCKET_NAME}"
if [ -n "${ACCOUNT}" ]; then
    echo " Account: ${ACCOUNT}"
fi
echo "=========================================================="

# 1. Enable Required Google Cloud APIs
echo "Enabling necessary GCP APIs..."
gcloud services enable \
    texttospeech.googleapis.com \
    storage.googleapis.com \
    translate.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}" \
    "${ACCOUNT_FLAG[@]}"

# 2. Ensure GCS Storage Bucket Exists
echo "Verifying GCS Bucket..."
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" "${ACCOUNT_FLAG[@]}" >/dev/null 2>&1; then
    echo "Creating bucket gs://${BUCKET_NAME}..."
    gcloud storage buckets create "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" --location="${REGION}" "${ACCOUNT_FLAG[@]}" || true
fi

# 3. Build Container via Cloud Build
echo "Building container image with Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}" "${ACCOUNT_FLAG[@]}" .

# 4. Deploy to Cloud Run
echo "Deploying service to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --platform=managed \
    --region="${REGION}" \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GCS_BUCKET_NAME=${BUCKET_NAME}" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --project="${PROJECT_ID}" \
    "${ACCOUNT_FLAG[@]}"

echo "=========================================================="
echo " Deployment Complete!"
gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --format="value(status.url)" --project="${PROJECT_ID}" "${ACCOUNT_FLAG[@]}"
echo "=========================================================="
