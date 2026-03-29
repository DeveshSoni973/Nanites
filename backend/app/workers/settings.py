from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.embed import embed_node


def get_redis_settings() -> RedisSettings:
    url = settings.REDIS_URL.replace("redis://", "")
    host_port, db_num = url.rsplit("/", 1)
    host, port = host_port.split(":")
    return RedisSettings(host=host, port=int(port), database=int(db_num))


class WorkerSettings:
    functions = [embed_node]
    redis_settings = get_redis_settings()
