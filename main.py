import asyncio
import logging
from core.gate import BIT, Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("2x1-mux")

    print(await a.get_output(i=[1, 0], s=1))

asyncio.run(main())
