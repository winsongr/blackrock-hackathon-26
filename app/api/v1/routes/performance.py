import time

import psutil
from fastapi import APIRouter

from app.core.state import start_time
from app.models.performance import PerformanceResponse

router = APIRouter(tags=["performance"])


@router.get("/performance", response_model=PerformanceResponse)
def performance() -> PerformanceResponse:
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    millis = int((elapsed % 1) * 1000)

    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    threads = process.num_threads()

    return PerformanceResponse(
        time=f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}",
        memory=f"{memory_mb:.2f} MB",
        threads=threads,
    )
