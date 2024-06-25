import asyncio
from collections import defaultdict
import glob
import logging
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
import yaml

BIT = Literal[0, 1]


class Gate(BaseModel):
    name: str
    inputs: list[str]
    outputs: list[str]
    gates: dict[str, str]
    wires: dict[str, str]
    _built_gates: dict[str, "Gate"] = {}

    __available__: dict[str, "Gate"] = {}

    def register(self):
        if self.name not in Gate.__available__:
            Gate.__available__[self.name] = self

        return self

    def build(self):
        for gate_name, gate_type in self.gates.items():
            self._built_gates[gate_name] = (
                Gate.__available__[gate_type].model_copy().build()
            )

        return self

    def _check_inputs(self, inputs: dict[str, BIT]) -> dict[str, BIT]:
        input_pins_set = set(self.inputs)
        input_keys_set = set(inputs.keys())

        extra_keys = input_keys_set - input_pins_set

        if len(extra_keys) > 0:
            raise Exception(f"unrecognized key(s): {', '.join(extra_keys)}")

        uninitialized_pins = input_pins_set - input_keys_set

        if len(uninitialized_pins) > 0:
            logging.warning(
                f"pin(s) <{', '.join(uninitialized_pins)}> are not initialized, defaulting to 0"
            )

        return defaultdict(lambda: 0, inputs)

    async def get_output(self, **inputs: BIT):
        inputs = self._check_inputs(inputs)

        outputs_to_go = set(self.outputs)
        outputs: dict[str, BIT] = {}

        current_inputs = inputs

        assigned_inputs = defaultdict(dict)

        while True:
            for k, v in current_inputs.items():
                wire_end = self.wires[k]

                if wire_end in self.outputs:
                    outputs_to_go.remove(wire_end)
                    outputs[wire_end] = v
                    continue

                gate_name, input_pin = wire_end.split(".")
                assigned_inputs[gate_name][input_pin] = v

            if len(outputs_to_go) == 0:
                break

            tasks = []
            gates_to_process = []
            for gate_name, gate_inputs in assigned_inputs.items():
                gate = self._built_gates[gate_name]
                if len(gate.inputs) > len(gate_inputs):
                    continue

                gates_to_process.append(gate_name)
                tasks.append(gate.get_output(**gate_inputs))

            outs = await asyncio.gather(*tasks)

            current_inputs = {}
            for i, gate_name in enumerate(gates_to_process):
                del assigned_inputs[gate_name]

                for out_name, out_val in outs[i].items():
                    current_inputs[f"{gate_name}.{out_name}"] = out_val

        return outputs

    @classmethod
    def from_file(cls, file_path: str | Path):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise Exception(f"file {file_path} does not exist")

        with open(file_path, "r") as gate_def:
            gate_dict = yaml.safe_load(gate_def)

        return cls.model_validate(gate_dict)

    @classmethod
    def discover(cls, base_dir: str | Path):
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)

        if not base_dir.exists():
            raise Exception(f"base directory {base_dir} does not exist")

        if not base_dir.is_dir():
            raise Exception(f"{base_dir} is not a directory")

        all_files = glob.glob(str(base_dir / "*.gate")) + glob.glob(
            str(base_dir / "**/*.gate")
        )

        gates: list[Gate] = []
        for path in all_files:
            name = Path(path).name.replace(".gate", "")
            logging.info(f"discovered gate {name}")
            gates.append(cls.from_file(path).register())

        for gate in gates:
            gate.build()

    @classmethod
    def by_name(cls, name: str):
        return cls.__available__[name]


class NotGate(Gate):
    def __init__(self):
        super().__init__(name="not", inputs=["i"], outputs=["o"], gates={}, wires={})
        self.register()

    async def get_output(self, **inputs: BIT):
        inputs = self._check_inputs(inputs)

        return {"o": 1 - inputs["i"]}


NotGate().register()


class OrGate(Gate):
    def __init__(self):
        super().__init__(
            name="or", inputs=["a", "b"], outputs=["o"], gates={}, wires={}
        )
        self.register()

    async def get_output(self, **inputs: BIT):
        inputs = self._check_inputs(inputs)

        return {"o": inputs["a"] | inputs["b"]}


OrGate().register()
