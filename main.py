import asyncio
import logging
from core.gate import BIT, Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("32b-register")

    i: list[BIT] = [*(0 for _ in range(29)), 1, 0, 1]
    print(a.readable_output_values)
    
    await a.get_output(e=0, i=i)
    print(a.readable_output_values)

    await a.get_output(e=1, i=i)
    print(a.readable_output_values)

    await a.get_output(e=0, i=[0 for _ in range(32)])
    print(a.readable_output_values)


asyncio.run(main())
