import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_tri_state_buffer():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("tri-state-buffer")

    initial_output = gate.output_values
    assert initial_output == {"o": 0}

    all_bits: list[BIT] = [0, 1]

    for e in all_bits:
        for i in all_bits:
            output = await gate.get_output(i=i, e=e)
            assert output == {"o": 0 if e == 0 else i}
