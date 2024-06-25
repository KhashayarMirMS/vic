#! /usr/bin/env python

import argparse
from pathlib import Path
import sys


parser = argparse.ArgumentParser(
    prog="vic",
    usage="vic new <name>",
    description="create new custom gate",
)

parser.add_argument("name")

args = parser.parse_args()

def_path = Path(f"./custom/{args.name}.gate")

if def_path.exists():
    overwrite = input(f"definition for gate {args.name} already exists. do you want to overwrite it? ([y]/n) ")

    if overwrite.strip() == 'n':
        sys.exit(0)


TAB = 2 * " "

with open(def_path, "w") as gate_def:
    gate_def.write(f"name: {args.name}\n")
    gate_def.write(f"inputs:\n{TAB}\n")
    gate_def.write(f"outputs:\n{TAB}\n")
    gate_def.write(f"gates:\n{TAB}\n")
    gate_def.write(f"wires:\n{TAB}\n")
