import pytest

from core.gate import Gate


@pytest.mark.asyncio
async def test_multiple():
    a = await Gate.by_name("or")
    b = await Gate.by_name("or")

    output = await a.get_output(a=1, b=0)
    assert output == {"o": 1}

    assert b.output_values == {"o": 0}
