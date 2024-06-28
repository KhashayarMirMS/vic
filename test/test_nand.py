import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_nand():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("nand")

    all_bits: list[BIT] = [0, 1]

    for a in all_bits:
        for b in all_bits:
            output = await gate.get_output(a=a, b=b)
            assert output == {"o": 1 - (a & b)}
