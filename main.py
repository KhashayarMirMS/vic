import asyncio
import logging
from typing import cast
from core.clock import Clock
from core.gate import BIT, Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    d_latch = Gate.by_name("d-latch")
    e: BIT = 0

    async def clock_callback():
        nonlocal e
        e = cast(BIT, 1 - e)
        logging.info(f"setting enable pin to {e=}")
        logging.info(await d_latch.get_output(e=e, d=1))

    clock = Clock.from_file("./clock.yaml")

    await clock.run(clock_callback)


asyncio.run(main())
