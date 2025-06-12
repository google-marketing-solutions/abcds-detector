"""Class that implements the creative provider to retrieve
creative uris from GCS
"""

from gcp_api_services.gcs_api_service import gcs_api_service


class GCSCreativeProvider:
    """Class that implements the creative provider to
    retrieve creative uris from GCS
    """

    def __init__(self):
        pass

    def get_creative_uris(self, uris: list[str]) -> any:
        """Expands any GCS URI entry that is a folder path into its files."""
        for uri in uris:
            if uri.endswith("/"):
                print(f"EXPANDING URI: {uri} \n")
                bucket, prefix = uri.replace("gs://", "").split("/", 1)
                for blob in (
                    gcs_api_service.get_client()
                    .get_bucket(bucket)
                    .list_blobs(prefix=prefix, delimiter="/")
                ):
                    if not blob.name.endswith("/"):
                        yield f"gs://{bucket}/{blob.name}"
            else:
                yield uri
