from redis.exceptions import RedisError

from app.api.dependencies import get_minio_client, get_redis_client


def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.1.0"


class AvailableRedis:
    def ping(self):
        return True


class UnavailableRedis:
    def ping(self):
        raise RedisError("connection failed")


class AvailableMinio:
    def list_buckets(self):
        return []


class UnavailableMinio:
    def list_buckets(self):
        raise RuntimeError("connection failed")


def test_redis_health_check(client):
    client.app.dependency_overrides[get_redis_client] = lambda: AvailableRedis()

    response = client.get("/api/v1/health/redis")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "redis"}

    client.app.dependency_overrides.clear()


def test_redis_health_check_unavailable(client):
    client.app.dependency_overrides[get_redis_client] = lambda: UnavailableRedis()

    response = client.get("/api/v1/health/redis")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unavailable", "service": "redis"}

    client.app.dependency_overrides.clear()


def test_minio_health_check(client):
    client.app.dependency_overrides[get_minio_client] = lambda: AvailableMinio()

    response = client.get("/api/v1/health/minio")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "minio"}

    client.app.dependency_overrides.clear()


def test_minio_health_check_unavailable(client):
    client.app.dependency_overrides[get_minio_client] = lambda: UnavailableMinio()

    response = client.get("/api/v1/health/minio")

    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "unavailable", "service": "minio"}

    client.app.dependency_overrides.clear()
