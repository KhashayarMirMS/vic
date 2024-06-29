import asyncio
import logging
from core.gate import Gate

logging.basicConfig(level=logging.WARNING)


async def main():
    await Gate.discover("./custom/")
    a = await Gate.by_name("s-r-latch")

    print(a.output_values)
    print("-" * 20)
    print("-" * 20)
    print(await a.get_output(s=1, r=0))
    print('-' * 20)
    print(await a.get_output(s=0, r=1))
    print("-" * 20)
    print(await a.get_output(s=0, r=0))
    print("-" * 20)
    print(await a.get_output(s=1, r=1))

    print()

    a = await Gate.by_name("s-r-nand-latch")

    print(a.output_values)
    print("-" * 20)
    print("-" * 20)
    print(await a.get_output(s=1, r=0))
    print("-" * 20)
    print(await a.get_output(s=0, r=1))
    print("-" * 20)
    print(await a.get_output(s=0, r=0))
    print("-" * 20)
    print(await a.get_output(s=1, r=1))
    
    print()

    a = await Gate.by_name("j-k-flip-flop")

    print(a.output_values)
    print("-" * 20)
    print("-" * 20)
    print(await a.get_output(j=1, k=0, clk=0))
    print(await a.get_output(j=1, k=0, clk=1))
    print("-" * 20)
    print(await a.get_output(j=0, k=1, clk=0))
    print(await a.get_output(j=0, k=1, clk=1))
    print("-" * 20)
    print(await a.get_output(j=0, k=0, clk=0))
    print(await a.get_output(j=0, k=0, clk=1))
    print("-" * 20)
    print(await a.get_output(j=1, k=1, clk=0))
    print(await a.get_output(j=1, k=1, clk=1))
    print()
    print(await a.get_output(j=1, k=1, clk=0))
    print(await a.get_output(j=1, k=1, clk=1))
    print()
    print(await a.get_output(j=1, k=1, clk=0))
    print(await a.get_output(j=1, k=1, clk=1))


asyncio.run(main())
