import json
import redis
from Backend.config import settings
# Redis Connection
redis_client = redis.Redis.from_url(settings.REDIS_URL,
    decode_responses=True
)


def set_progress(
    ref_id: str,
    step: str,
    step_no: int,
    total_steps: int,
    status: str = "Processing",
    message: str = ""
):
    """
    Store current processing status in Redis.
    """

    data = {
        "status": status,
        "step": step,
        "step_no": step_no,
        "total_steps": total_steps,
        "progress": int((step_no / total_steps) * 100),
        "message": message
    }

    redis_client.set(
        f"progress:{ref_id}",
        json.dumps(data)
    )

    # Automatically remove after 30 minutes
    redis_client.expire(
        f"progress:{ref_id}",
        1800
    )


def get_progress(ref_id: str):
    """
    Read processing status from Redis.
    """

    data = redis_client.get(f"progress:{ref_id}")

    if not data:
        return None

    return json.loads(data)


def complete_progress(ref_id: str):
    """
    Mark processing completed.
    """

    data = {
        "status": "Completed",
        "step": "Completed",
        "step_no": 7,
        "total_steps": 7,
        "progress": 100,
        "message": "Drawing processed successfully."
    }

    redis_client.set(
        f"progress:{ref_id}",
        json.dumps(data)
    )

    redis_client.expire(
        f"progress:{ref_id}",
        300
    )


def failed_progress(ref_id: str, error: str):
    """
    Mark processing failed.
    """

    data = {
        "status": "Failed",
        "step": "Failed",
        "step_no": 0,
        "total_steps": 7,
        "progress": 0,
        "message": error
    }

    redis_client.set(
        f"progress:{ref_id}",
        json.dumps(data)
    )

    redis_client.expire(
        f"progress:{ref_id}",
        300
    )


def clear_progress(ref_id: str):
    """
    Remove processing information.
    """

    redis_client.delete(f"progress:{ref_id}")