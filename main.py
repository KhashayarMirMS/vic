import asyncio
import logging
from typing import cast
from core.clock import Clock
from core.gate import BIT, Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    a = Gate.by_name("3b-nand")

    print(await a.get_output(a=1, b=1, c=0))
    print(await a.get_output(a=1, b=1, c=1))


asyncio.run(main())
