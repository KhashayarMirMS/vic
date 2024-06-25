import asyncio
import logging
from core.gate import Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    a = Gate.by_name("tristatebuffer")
    print(await a.get_output(i=0, e=0))


asyncio.run(main())
