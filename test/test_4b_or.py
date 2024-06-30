import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_4b_or():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("4b-or")

    initial_output = gate.output_values
    assert initial_output == {"o": 0}

    all_bits: list[BIT] = [0, 1]

    for a in all_bits:
        for b in all_bits:
            for c in all_bits:
                for d in all_bits:
                    output = await gate.get_output(i=[a, b, c, d])
                    assert output == {"o": a | b | c | d}