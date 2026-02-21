from pydantic import BaseModel


class PerformanceResponse(BaseModel):
    time: str
    memory: str
    threads: int
