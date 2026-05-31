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
        self.upload_bytes(
            bucket_name=bucket_name,
            object_key=object_key,
            content=content,
            content_type="application/pdf",
        )

    def upload_bytes(
        self,
        *,
        bucket_name: str,
        object_key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        self.ensure_bucket(bucket_name)
        self.client.put_object(
            bucket_name,
            object_key,
            BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

    def get_object_bytes(self, *, bucket_name: str, object_key: str) -> bytes:
        response = self.client.get_object(bucket_name, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
