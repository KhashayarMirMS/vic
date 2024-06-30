import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_2x1_mux():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("2x1-mux")

    all_bits: list[BIT] = [0, 1]

    for x in all_bits:
        i: list[BIT] = [0 if y == x else 1 for y in range(2)]
        s = x

        output = await gate.get_output(i=i, s=s)
        assert output == {"y": 0}
