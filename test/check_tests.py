import glob
from pathlib import Path


gate_list = list(
    map(lambda p: Path(p).name.replace(".gate", ""), glob.glob("./custom/*.gate"))
) + ["or", "not"]

test_list = map(
    lambda p: Path(p).name.replace("test_", "").replace(".py", ""),
    glob.glob("./test/*.py"),
)

diff = set(gate_list) - set(test_list)

TAB = "  "
print(f"{len(diff)} gates are missing tests:", end=f"\n{TAB}")
print(f"\n{TAB}".join(diff))
