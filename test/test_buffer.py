import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_buffer():
    await Gate.discover("./custom/")
    gate = await Gate.by_name("buffer")

    initial_output = gate.output_values
    assert initial_output == {"o": 0}

    all_bits: list[BIT] = [0, 1]

    for i in all_bits:
        output = await gate.get_output(i=i)
        assert output == {"o": i}
