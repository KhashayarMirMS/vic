import asyncio
import logging
from core.clock import Clock
from core.gate import Gate

logging.basicConfig(level=logging.INFO)


async def main():
    Gate.discover("./custom/")
    one_bit_adder = Gate.by_name("full-adder")

    adding_list = []

    for a in [0, 1]:
        for b in [0, 1]:
            for ci in [0, 1]:
                adding_list.append((a, b, ci))

    i = 0

    async def clock_callback():
        nonlocal i

        a, b, ci = adding_list[i]
        print(f"{a=}, {b=}, {ci=}")
        logging.info(await one_bit_adder.get_output(a=a, b=b, ci=ci))

        i += 1

    clock = Clock.from_file("./clock.yaml")

    await clock.run(clock_callback)


asyncio.run(main())
