import asyncio
import inspect
from pathlib import Path
from typing import Awaitable, Callable, cast
from pydantic import BaseModel
import yaml

from core.gate import BIT, Pin

CLOCK_CALLBACK = Callable[[BIT], None | Awaitable[None]]


class Clock(BaseModel):
    tick_speed: float = 0.01
    max_ticks: int | None = None

    _pin: Pin = Pin()

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
            await asyncio.sleep(self.tick_speed)

            new_value = cast(BIT, 1 - self._pin.value)
            await self._pin.set_value(new_value)

            result = callback(new_value)
            if inspect.isawaitable(result):
                await result

            tick += 1
