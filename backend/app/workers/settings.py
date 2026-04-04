import logging

from arq.connections import RedisSettings

from app.core.config import settings
from app.ml.model import get_model
from app.workers.embed import embed_node

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def get_redis_settings() -> RedisSettings:
    url = settings.REDIS_URL.replace("redis://", "")
    host_port, db_num = url.rsplit("/", 1)
    host, port = host_port.split(":")
    return RedisSettings(host=host, port=int(port), database=int(db_num))


async def on_startup(ctx: dict) -> None:
    logger.info("Initializing worker, pre-loading model...")
    # Pre-load the model once to avoid overhead during job processing
    get_model()
    logger.info("Worker initialization complete.")


class WorkerSettings:
    functions = [embed_node]
    on_startup = on_startup
    redis_settings = get_redis_settings()
    max_jobs = 1
