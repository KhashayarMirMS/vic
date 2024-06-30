import asyncio
import logging
from core.gate import BIT, Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("4x1-mux")

    print(await a.get_output(i=[0, 1, 1, 1], s=[0, 0]))

asyncio.run(main())
