import asyncio
import logging
from typing import cast
from core.gate import BIT, Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    a = Gate.by_name("d-latch")

    e: BIT = 0
    for i in range(10):
        if i % 2 == 0:
            e = cast(BIT, 1 - e)
        print(await a.get_output(e=e, d=0))


asyncio.run(main())
