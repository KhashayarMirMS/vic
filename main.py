import asyncio
import logging
from core.gate import BIT, Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    gate = await Gate.by_name("32b-full-adder-subtractor")
    a: list[BIT] = [1, 0, 1, *(0 for _ in range(29))]
    b: list[BIT] = [1, 0, 0, *(0 for _ in range(29))]

    await gate.get_output(a=a, b=b, ci=1)
    print(gate.readable_output_values)

asyncio.run(main())
