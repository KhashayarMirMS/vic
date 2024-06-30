import random
from typing import cast
import pytest

from core.gate import BIT, Gate


def to_bits(n: int) -> list[BIT]:
    return list(map(lambda c: cast(BIT, int(c)), f"{n:032b}"))


@pytest.mark.asyncio
async def test_32b_register():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("32b-register")

    i = random.getrandbits(32)
    i_bits = to_bits(i)

    await gate.get_output(e=1, i=i_bits)
    await gate.get_output(e=0, i=[0 for _ in range(32)])

    output_bits = gate.readable_output_values["o"]
    output_string = "".join(map(lambda i: str(i), cast(list[BIT], output_bits)))
    output_int = int(output_string, 2)

    assert output_int == i
