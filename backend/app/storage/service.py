from io import BytesIO

from minio import Minio


class ObjectStorageService:
    def __init__(self, client: Minio) -> None:
        self.client = client

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def upload_pdf(
        self,
        *,
        bucket_name: str,
        object_key: str,
        content: bytes,
    ) -> None:
        self.ensure_bucket(bucket_name)
        self.client.put_object(
            bucket_name,
            object_key,
            BytesIO(content),
            length=len(content),
            content_type="application/pdf",
        )
