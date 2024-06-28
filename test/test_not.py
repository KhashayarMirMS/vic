import pytest

from core.gate import Gate


@pytest.mark.asyncio
async def test_not():
    g = await Gate.by_name("not")

    initial_output = g.output_values
    assert initial_output == {"o": 1}

    output = await g.get_output(i=1)
    assert output == {"o": 0}

    output = await g.get_output(i=0)
    assert output == {"o": 1}
