import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_full_adder():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("full-adder")

    initial_output = gate.output_values
    assert initial_output == {"s": 0, "co": 0}

    all_bits: list[BIT] = [0, 1]

    for a in all_bits:
        for b in all_bits:
            for ci in all_bits:
                output = await gate.get_output(a=a, b=b, ci=ci)

                _sum = a + b + ci
                expected_s = _sum % 2
                expected_co = _sum // 2

                assert output == {"s": expected_s, "co": expected_co}
