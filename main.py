import asyncio
import logging
from core.gate import Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("gated-s-r-latch")
    print(a.output_values)
    print(await a.get_output(s=1, r=0, e=0))
    print(await a.get_output(s=1, r=0, e=1))
    print(await a.get_output(s=1, r=0, e=0))

    print()

    a = await Gate.by_name("master-slave-s-r-flip-flop")
    print(a.output_values)
    print(await a.get_output(s=1, r=0, clk=0))
    print(await a.get_output(s=1, r=0, clk=1))
    print(await a.get_output(s=1, r=0, clk=0))


asyncio.run(main())
