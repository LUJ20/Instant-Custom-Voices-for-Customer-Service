#!/usr/bin/env bash
# Copyright 2026 Google LLC
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
ACCOUNT="${3:-${GCP_AUTH_ACCOUNT:-$(gcloud config get-value account 2>/dev/null || echo '')}}"
SERVICE_NAME="instant-custom-voice-cust-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
    echo "ERROR: Please specify a project ID as an argument or set GOOGLE_CLOUD_PROJECT."
    echo "Usage: ./redeploy.sh [PROJECT_ID] [REGION] [ACCOUNT]"
    exit 1
fi

ACCOUNT_FLAG=()
if [ -n "${ACCOUNT}" ] && [ "${ACCOUNT}" != "(unset)" ]; then
    ACCOUNT_FLAG=("--account=${ACCOUNT}")
fi

echo "Quick redeploying ${SERVICE_NAME} to ${PROJECT_ID} (Region: ${REGION})..."
gcloud builds submit --tag "${IMAGE_NAME}" --project="${PROJECT_ID}" "${ACCOUNT_FLAG[@]}" .
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --platform=managed \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    "${ACCOUNT_FLAG[@]}"
