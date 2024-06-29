from typing import cast
import pytest
import random

from core.gate import BIT, Gate


def to_bits(n: int) -> list[BIT]:
    return list(map(lambda c: cast(BIT, int(c)), reversed(f"{n:032b}")))


@pytest.mark.asyncio
async def test_32b_full_adder():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("32b-full-adder")
    initial_output = gate.readable_output_values
    assert initial_output == {"co": 0, "s": [0 for _ in range(32)]}

    for _ in range(10):
        # NOTE this is bad practice since tests are not reproducible
        a = random.getrandbits(32)
        b = random.getrandbits(32)

        a, b = max(a, b), min(a, b)
        diff = a - b
        _sum, a = a, diff

        # NOTE try to negate the bad practice by printing the parameters
        print(f"{a=}, {b=}, {_sum=}")

        a_bits = to_bits(a)
        b_bits = to_bits(b)

        await gate.get_output(a=a_bits, b=b_bits, ci=0)
        output = gate.readable_output_values

        assert output["co"] == 0
        reversed_s = "".join(map(lambda i: str(i), reversed(cast(list[BIT], output["s"]))))
        output_sum = int(reversed_s, 2)

        assert output_sum == _sum
