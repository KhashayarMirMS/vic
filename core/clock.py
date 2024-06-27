import asyncio
import inspect
from pathlib import Path
from typing import Awaitable, Callable
from pydantic import BaseModel
import yaml

CLOCK_CALLBACK = Callable[[], None | Awaitable[None]]


class Clock(BaseModel):
    speed: float = 0.01
    max_ticks: int | None = None

    @classmethod
    def from_file(cls, file_path: str | Path):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise Exception(f"file {file_path} does not exist")

        with open(file_path, "r") as gate_def:
            gate_dict = yaml.safe_load(gate_def)

        return cls.model_validate(gate_dict)

    async def run(self, callback: CLOCK_CALLBACK):
        max_ticks = self.max_ticks or float("inf")
        tick = 0

        while tick < max_ticks:
            await asyncio.sleep(self.speed)
            
            result = callback()
            if inspect.isawaitable(result):
                await result

            tick += 1
