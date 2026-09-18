"""
Copyright 2026 Google LLC
Author: Layolin Jesudhass <layolin@google.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import logging
from typing import Optional, Tuple
import google.auth
from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger("gcs_service")

DEFAULT_BUCKET_NAME = os.getenv(
    "GCS_BUCKET_NAME",
    f"{os.getenv('GOOGLE_CLOUD_PROJECT', 'consumer-genai-experiments')}-cust-service-voice"
)


class GCSService:
    """Manages Google Cloud Storage uploads and asset persistence."""

    def __init__(self, bucket_name: Optional[str] = None, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME") or (f"{self.project_id}-cust-service-voice" if self.project_id else "")
        self.session = None
        self._init_client()

    def _init_client(self):
        try:
            credentials, default_project = google.auth.default()
            self.session = AuthorizedSession(credentials)
            if not self.project_id:
                self.project_id = default_project
            if not self.bucket_name and self.project_id:
                self.bucket_name = f"{self.project_id}-cust-service-voice"
        except Exception as e:
            logger.warning("Google Auth initialization fallback for GCS: %s", e)
            self.session = None

    def ensure_bucket_exists(self) -> bool:
        """Verifies or creates the target GCS bucket via GCS REST API."""
        if not self.session:
            return False
        try:
            url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket_name}"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return True
            elif resp.status_code == 404:
                # Create bucket
                create_url = f"https://storage.googleapis.com/storage/v1/b?project={self.project_id}"
                body = {"name": self.bucket_name, "location": "US"}
                create_resp = self.session.post(create_url, json=body, timeout=15)
                return create_resp.status_code in (200, 201)
        except Exception as e:
            logger.warning("Could not verify/create GCS bucket: %s", e)
        return False

    def upload_bytes(
        self,
        data: bytes,
        destination_blob_name: str,
        content_type: str = "audio/mpeg"
    ) -> Tuple[bool, str]:
        """Uploads raw bytes to GCS via REST API and returns (success, gcs_uri_or_path)."""
        if not self.session:
            # Local fallback path
            local_dir = os.path.join("/tmp", "voice_agent_cache")
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, os.path.basename(destination_blob_name))
            with open(local_path, "wb") as f:
                f.write(data)
            return True, local_path

        try:
            upload_url = f"https://storage.googleapis.com/upload/storage/v1/b/{self.bucket_name}/o?uploadType=media&name={destination_blob_name}"
            headers = {"Content-Type": content_type}
            resp = self.session.post(upload_url, data=data, headers=headers, timeout=30)
            if resp.status_code in (200, 201):
                gcs_uri = f"gs://{self.bucket_name}/{destination_blob_name}"
                logger.info("Uploaded %d bytes to %s", len(data), gcs_uri)
                return True, gcs_uri
            else:
                logger.warning("GCS REST upload returned %d: %s. Using local fallback.", resp.status_code, resp.text)
        except Exception as e:
            logger.error("GCS Upload failed for %s: %s", destination_blob_name, e)

        # Fallback to local persistence
        local_dir = os.path.join("/tmp", "voice_agent_cache")
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, os.path.basename(destination_blob_name))
        with open(local_path, "wb") as f:
            f.write(data)
        return True, local_path

    def upload_audio_bytes(self, data: bytes, destination_blob_name: str) -> str:
        """Uploads audio bytes and returns the resulting URI or path."""
        _, uri = self.upload_bytes(data, destination_blob_name, content_type="audio/mpeg")
        return uri

    def upload_json(self, data: dict, destination_blob_name: str) -> Tuple[bool, str]:
        """Uploads a dictionary as JSON to GCS."""
        import json
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        return self.upload_bytes(json_bytes, destination_blob_name, content_type="application/json")

    def list_blobs(self, prefix: str = "") -> list:
        """Lists blob names matching prefix in the GCS bucket."""
        if not self.session or not self.bucket_name:
            return []
        try:
            url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket_name}/o"
            params = {}
            if prefix:
                params["prefix"] = prefix
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                return [it["name"] for it in items if "name" in it]
        except Exception as e:
            logger.warning("GCS list_blobs failed for prefix '%s': %s", prefix, e)
        return []

    def download_bytes(self, blob_name: str) -> Optional[bytes]:
        """Downloads raw bytes of a blob from GCS."""
        if not self.session or not self.bucket_name:
            return None
        try:
            import urllib.parse
            encoded_name = urllib.parse.quote(blob_name, safe="")
            url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket_name}/o/{encoded_name}?alt=media"
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.content
            else:
                logger.warning("GCS download_bytes %s returned status %d", blob_name, resp.status_code)
        except Exception as e:
            logger.error("GCS download_bytes failed for %s: %s", blob_name, e)
        return None

    def download_json(self, blob_name: str) -> Optional[dict]:
        """Downloads and parses a JSON blob from GCS."""
        raw_bytes = self.download_bytes(blob_name)
        if raw_bytes:
            try:
                import json
                return json.loads(raw_bytes.decode("utf-8"))
            except Exception as e:
                logger.error("Failed to decode JSON for %s: %s", blob_name, e)
        return None

    def delete_blob(self, blob_name: str) -> bool:
        """Deletes a blob from GCS."""
        if not self.session or not self.bucket_name:
            return False
        try:
            import urllib.parse
            encoded_name = urllib.parse.quote(blob_name, safe="")
            url = f"https://storage.googleapis.com/storage/v1/b/{self.bucket_name}/o/{encoded_name}"
            resp = self.session.delete(url, timeout=15)
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.warning("GCS delete_blob failed for %s: %s", blob_name, e)
        return False

