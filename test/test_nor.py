import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_nor():
    Gate.from_file("./custom/nor.gate").register()
    g = await Gate.by_name("nor")

    await g._built_gates["or"].pins["o"].set_value(0)

    initial_output = g.output_values
    assert initial_output == {"o": 1}

    all_bits: list[BIT] = [0, 1]

    for a in all_bits:
        for b in all_bits:
            output = await g.get_output(a=a, b=b)
            assert output == {"o": 1 - (a | b)}
