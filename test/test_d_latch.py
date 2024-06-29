import pytest

from core.gate import BIT, Gate


@pytest.mark.asyncio
async def test_d_latch():
    await Gate.discover("./custom/")

    gate = await Gate.by_name("d-latch")

    all_bits: list[BIT] = [0, 1]

    last_q = gate.output_values["q"]

    for e in all_bits:
        for d in all_bits:
            output = await gate.get_output(d=d, e=e)

            expected = {"q": d, "~q": 1 - d}
            if e == 0:
                expected = {"q": last_q, "~q": 1 - last_q}

            assert output == expected
            last_q = output["q"]
