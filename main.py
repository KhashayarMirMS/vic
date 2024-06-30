import asyncio
import logging
from core.gate import BIT, Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("4b-or")

    print(await a.get_output(i=[0, 0, 0, 1]))

asyncio.run(main())
