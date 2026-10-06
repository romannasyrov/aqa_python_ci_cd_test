import os
import uuid


def get_worker_id() -> str:
    """Возвращает 'gw0', 'gw1', ... или 'master'."""
    return os.getenv("PYTEST_XDIST_WORKER", "master")


def worker_scoped_id(base: str) -> str:
    """
    Генерирует worker-scoped уникальный ID.

    Примеры:
        worker_scoped_id("post") -> "post_gw0_a1b2c3d4"
    """
    worker = get_worker_id()
    unique = uuid.uuid4().hex[:8]
    return f"{base}_{worker}_{unique}"