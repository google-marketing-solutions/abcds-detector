"""Service that interacts with the Google Cloud Storage API"""

import json
from google.cloud import storage
from configuration import Configuration


class GCSAPIService:
    """Service that interacts with the Google Cloud Storage API"""

    def __init__(self):
        self.client = storage.Client()

    def get_client(self):
        return self.client

    def get_annotation_uri(self, config: Configuration, video_uri: str) -> str:
        """Helper to translate video to annotation uri."""
        return (
            video_uri.replace("gs://", config.annotation_path).replace(".", "_") + "/"
        )

    def get_reduced_uri(self, config: Configuration, video_uri: str) -> str:
        """Helper to translate video to reduced video uri."""
        return self.get_annotation_uri(config, video_uri) + "reduced_1st_5_secs.mp4"

    def get_blob(self, uri: str) -> any:
        """Return GCS blob object from full uri."""
        bucket, path = uri.replace("gs://", "").split("/", 1)
        return  self.client.get_bucket(bucket).get_blob(path)

    def upload_blob(self, uri: str, file_path: str) -> any:
        """Uploads GCS blob object from file."""
        bucket, path = uri.replace("gs://", "").split("/", 1)
        self.client.get_bucket(bucket).blob(path).upload_from_filename(file_path)

    def load_blob(self, annotation_uri: str):
        """Loads a blob to json"""
        blob = self.get_blob(annotation_uri)
        blob_json = json.loads(blob.download_as_string()).get("annotation_results")[0]
        return blob_json

    def get_video_name_from_uri(self, uri: str):
        """Gets the video name from the video uri"""
        video_parts = uri.split("/")
        if len(video_parts) > 0:
            # Video name is the last element
            return video_parts[-1]
        return ""


gcs_api_service = GCSAPIService()
