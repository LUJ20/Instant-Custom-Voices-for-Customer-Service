"""
Copyright 2026 Google LLC

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
import json
import time
import logging
from typing import List, Dict, Any, Optional
from gcs_service import GCSService

logger = logging.getLogger("project_manager")


class ProjectManager:
    """Manages project persistence (Save, Load, List, Delete) in GCS and local cache for customer service voice demos."""

    def __init__(
        self,
        projects_dir: Optional[str] = None,
        gcs_service: Optional[GCSService] = None,
        gcs_bucket: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        self.projects_dir = projects_dir or os.path.join(os.path.dirname(__file__), "saved_projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        if gcs_service:
            self.gcs_service = gcs_service
        else:
            self.gcs_service = GCSService(bucket_name=gcs_bucket, project_id=project_id)

    def set_gcs_config(self, bucket_name: Optional[str] = None, project_id: Optional[str] = None):
        """Updates GCS service configuration if project or bucket changes at runtime."""
        if bucket_name or project_id:
            self.gcs_service = GCSService(bucket_name=bucket_name, project_id=project_id)

    def save_project(
        self,
        name: str,
        scenario_prompt: str = "",
        dialogue_turns: Optional[List[Dict[str, Any]]] = None,
        dialogue: Optional[List[Dict[str, Any]]] = None,
        timeline: Optional[List[Dict[str, Any]]] = None,
        agent_voice_id: Optional[str] = None,
        customer_voice_id: Optional[str] = None,
        target_translation_lang: Optional[str] = None,
        conversation_language: Optional[str] = None,
        gcs_audio_uri: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Saves a project manifest, timeline, and audio artifact to GCS and local disk."""
        turns = dialogue_turns if dialogue_turns is not None else (dialogue or [])
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name).strip("_")
        timestamp = int(time.time())
        proj_id = f"proj_{safe_name}_{timestamp}"

        selected_lang = conversation_language or target_translation_lang or "English (US)"

        manifest = {
            "project_id": proj_id,
            "name": name,
            "scenario_prompt": scenario_prompt,
            "dialogue": turns,
            "dialogue_turns": turns,
            "timeline": timeline,
            "agent_voice_id": agent_voice_id,
            "customer_voice_id": customer_voice_id,
            "target_translation_lang": selected_lang,
            "conversation_language": selected_lang,
            "gcs_audio_uri": gcs_audio_uri,
            "created_at": timestamp,
            "formatted_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        }

        # 1. Local Cache Persistence
        manifest_path = os.path.join(self.projects_dir, f"{proj_id}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        if audio_bytes:
            audio_path = os.path.join(self.projects_dir, f"{proj_id}.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)

        # 2. Permanent Google Cloud Storage Persistence
        if self.gcs_service and self.gcs_service.session:
            try:
                # Save audio to GCS
                if audio_bytes:
                    gcs_audio_blob = f"projects/{proj_id}.mp3"
                    _, gcs_audio_url = self.gcs_service.upload_bytes(
                        audio_bytes, gcs_audio_blob, content_type="audio/mpeg"
                    )
                    manifest["gcs_audio_uri"] = gcs_audio_url

                # Save JSON manifest to GCS
                gcs_manifest_blob = f"projects/{proj_id}.json"
                ok, gcs_manifest_url = self.gcs_service.upload_json(manifest, gcs_manifest_blob)
                if ok:
                    manifest["gcs_manifest_uri"] = gcs_manifest_url
                    logger.info("Successfully persisted project %s to GCS: %s", proj_id, gcs_manifest_url)
            except Exception as e:
                logger.error("Failed to upload project %s to GCS: %s", proj_id, e)

        logger.info("Saved project %s locally and to Cloud Storage", proj_id)
        return manifest

    def list_projects(self) -> List[Dict[str, Any]]:
        """Lists all saved projects from GCS and local storage sorted by creation date descending."""
        projects_dict: Dict[str, Dict[str, Any]] = {}

        # 1. Fetch from Google Cloud Storage
        if self.gcs_service and self.gcs_service.session:
            try:
                blobs = self.gcs_service.list_blobs(prefix="projects/")
                for blob_name in blobs:
                    if blob_name.endswith(".json"):
                        filename = os.path.basename(blob_name)
                        local_cache_path = os.path.join(self.projects_dir, filename)
                        
                        data = None
                        # Check local cache first
                        if os.path.exists(local_cache_path):
                            try:
                                with open(local_cache_path, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                            except Exception:
                                data = None

                        # If not cached or corrupted, fetch directly from GCS
                        if not data:
                            data = self.gcs_service.download_json(blob_name)
                            if data:
                                # Save to local cache for fast loading
                                try:
                                    with open(local_cache_path, "w", encoding="utf-8") as f:
                                        json.dump(data, f, indent=2, ensure_ascii=False)
                                except Exception as e:
                                    logger.warning("Could not write local cache for %s: %s", filename, e)

                        if data and "project_id" in data:
                            projects_dict[data["project_id"]] = data
            except Exception as e:
                logger.warning("Failed to list projects from GCS: %s", e)

        # 2. Check local disk for any additional projects
        if os.path.exists(self.projects_dir):
            for filename in os.listdir(self.projects_dir):
                if filename.endswith(".json"):
                    manifest_path = os.path.join(self.projects_dir, filename)
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            pid = data.get("project_id", filename.replace(".json", ""))
                            if pid not in projects_dict:
                                projects_dict[pid] = data
                    except Exception as e:
                        logger.warning("Could not read local project file %s: %s", filename, e)

        project_list = list(projects_dict.values())
        project_list.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return project_list

    def _resolve_project_id(self, identifier: str) -> Optional[str]:
        """Resolves identifier from either project_id or name."""
        if os.path.exists(os.path.join(self.projects_dir, f"{identifier}.json")):
            return identifier
        for p in self.list_projects():
            if p.get("name") == identifier or p.get("project_id") == identifier:
                return p.get("project_id")
        return None

    def load_project(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Loads a project manifest and reads its audio bytes from GCS or local disk."""
        proj_id = self._resolve_project_id(identifier) or identifier

        manifest = None
        manifest_path = os.path.join(self.projects_dir, f"{proj_id}.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception as e:
                logger.warning("Error reading local manifest %s: %s", manifest_path, e)

        # If not on local disk, fetch from GCS
        if not manifest and self.gcs_service and self.gcs_service.session:
            manifest = self.gcs_service.download_json(f"projects/{proj_id}.json")
            if manifest:
                try:
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(manifest, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

        if not manifest:
            logger.error("Could not find manifest for project %s", proj_id)
            return None

        # Load Audio Bytes
        audio_bytes = self.get_project_audio(proj_id)
        manifest["audio_bytes"] = audio_bytes
        return manifest

    def get_project_audio(self, identifier: str) -> Optional[bytes]:
        """Retrieves stored MP3 audio bytes for a given project ID from local disk or GCS."""
        proj_id = self._resolve_project_id(identifier) or identifier
        audio_path = os.path.join(self.projects_dir, f"{proj_id}.mp3")

        # 1. Local Cache Check
        if os.path.exists(audio_path):
            try:
                with open(audio_path, "rb") as af:
                    return af.read()
            except Exception as e:
                logger.warning("Failed reading local audio for %s: %s", proj_id, e)

        # 2. Download from GCS
        if self.gcs_service and self.gcs_service.session:
            try:
                data = self.gcs_service.download_bytes(f"projects/{proj_id}.mp3")
                if data:
                    # Cache locally
                    try:
                        with open(audio_path, "wb") as af:
                            af.write(data)
                    except Exception:
                        pass
                    return data
            except Exception as e:
                logger.error("Failed to download audio from GCS for %s: %s", proj_id, e)

        return None

    def delete_project(self, identifier: str) -> bool:
        """Deletes a saved project and its associated audio file from GCS and local disk."""
        proj_id = self._resolve_project_id(identifier) or identifier
        deleted = False

        # 1. Delete from local disk
        manifest_path = os.path.join(self.projects_dir, f"{proj_id}.json")
        audio_path = os.path.join(self.projects_dir, f"{proj_id}.mp3")

        if os.path.exists(manifest_path):
            try:
                os.remove(manifest_path)
                deleted = True
            except Exception:
                pass
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                deleted = True
            except Exception:
                pass

        # 2. Delete from GCS
        if self.gcs_service and self.gcs_service.session:
            try:
                ok1 = self.gcs_service.delete_blob(f"projects/{proj_id}.json")
                ok2 = self.gcs_service.delete_blob(f"projects/{proj_id}.mp3")
                if ok1 or ok2:
                    deleted = True
            except Exception as e:
                logger.warning("GCS deletion error for %s: %s", proj_id, e)

        return deleted
