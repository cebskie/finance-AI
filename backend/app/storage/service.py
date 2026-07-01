from supabase import Client


class ObjectStorageService:
    def __init__(self, client: Client):
        self.client = client

    def ensure_bucket(self, bucket_name: str) -> None:
        # Bucket is managed in Supabase dashboard.
        pass

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
        self.client.storage.from_(bucket_name).upload(
            path=object_key,
            file=content,
            file_options={
                "content-type": content_type,
                "upsert": "true",
            }
        )

    def get_object_bytes(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        return self.client.storage.from_(bucket_name).download(object_key)