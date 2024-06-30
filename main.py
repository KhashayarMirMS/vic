import asyncio
import logging
from core.gate import BIT, Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("8x1-mux")

    print(await a.get_output(i=[1, 1, 0, 1, 1, 1, 1, 1], s=[0, 1, 0]))

asyncio.run(main())
