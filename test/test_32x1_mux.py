from typing import cast
import pytest

from core.gate import BIT, Gate


def to_bits(n: int) -> list[BIT]:
    return list(map(lambda c: cast(BIT, int(c)), reversed(f"{n:05b}")))


@pytest.mark.asyncio
async def test_32x1_mux():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("32x1-mux")

    for x in range(32):
        i: list[BIT] = [0 if y == x else 1 for y in range(32)]
        s = to_bits(x)

        output = await gate.get_output(i=i, s=s)
        assert output == {"y": 0}

        i: list[BIT] = [1 if y == x else 0 for y in range(32)]
        s = to_bits(x)

        output = await gate.get_output(i=i, s=s)
        assert output == {"y": 1}
