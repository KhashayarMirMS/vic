import asyncio
import logging
from typing import cast
from core.clock import Clock
from core.gate import BIT, Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    full_adder = Gate.by_name("32b-full-adder")

    a: list[BIT] = [0 for _ in range(32)]
    
    ci = 1

    async def clock_callback():
        b: list[BIT] = cast(list[BIT], full_adder.readable_output_values.get("s"))
        await full_adder.get_output(a=a, b=b, ci=ci)

        logging.info(full_adder.readable_output_values)

    clock = Clock.from_file("./clock.yml")

    await clock.run(clock_callback)


asyncio.run(main())
