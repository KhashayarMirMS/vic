import asyncio
import logging
from core.gate import Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    a = Gate.by_name("and")
    print(await a.get_output(a=1, b=1))


asyncio.run(main())
