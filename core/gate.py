import asyncio
from collections import defaultdict
import glob
import logging
from pathlib import Path
from typing import Any, Literal, cast
from pydantic import BaseModel, field_validator
import yaml
import re

BIT = Literal[0, 1]

array_definition_regex = re.compile("(?P<name>.+)\\[(?P<size>\\d+)\\]")
range_definition_regex = re.compile(
    "\\((?P<name>\\w+)=(?P<start>\\d+)\\.\\.(?P<end>\\d+)\\)"
)
expression_regex = re.compile("#\\((?P<expression>.*)\\)")


def _compile_range_script(script: str, context: dict[str, Any]):
    for key, value in context.items():
        script = re.sub(f"#{key}", str(value), script)

    def evaluate_expression(match: re.Match[str]):
        return str(eval(match.group("expression"), context))

    return re.sub(expression_regex, evaluate_expression, script)


class Gate(BaseModel):
    name: str
    inputs: list[str]
    outputs: list[str]
    gates: dict[str, str]
    wires: dict[str, str | list[str]]
    _built_gates: dict[str, "Gate"] = {}
    _output_values: dict[str, BIT] = {}

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

        for output_name in self.outputs:
            self._output_values[output_name] = 0

        return self

    def _check_inputs(self, raw_inputs: dict[str, BIT | list[BIT]]) -> dict[str, BIT]:
        inputs = {}

        for key, value in raw_inputs.items():
            if isinstance(value, int):
                inputs[key] = value
                continue

            for i, bit in enumerate(value):
                inputs[f"{key}[{i}]"] = bit

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

    @field_validator("inputs", "outputs", mode="before")
    def _parse_inputs_outputs(cls, values: list[str]):
        parsed_values = []
        for value in values:
            array_match = array_definition_regex.match(value)

            if array_match is None:
                parsed_values.append(value)
                continue

            name = array_match.group("name")
            size = int(array_match.group("size"))

            for i in range(size):
                parsed_values.append(f"{name}[{i}]")

        return parsed_values

    @field_validator("gates", mode="before")
    def _parse_gates(cls, values: dict[str, str]):
        parsed_values: dict[str, str] = {}
        for key, value in values.items():
            array_match = array_definition_regex.match(key)

            if array_match is None:
                parsed_values[key] = value
                continue

            name = array_match.group("name")
            size = int(array_match.group("size"))

            for i in range(size):
                parsed_values[f"{name}[{i}]"] = value

        return parsed_values

    @field_validator("wires", mode="before")
    def _parse_wires(
        cls, values: dict[str, str | list[str] | dict[str, str | list[str]]]
    ):
        parsed_values: dict[str, str | list[str]] = {}

        for key, value in values.items():
            if isinstance(value, str):
                parsed_values[key] = value
                continue

            if isinstance(value, list):
                parsed_values[key] = value
                continue

            range_match = range_definition_regex.match(key)

            if range_match is None:
                raise Exception(f"invalid range definition {key}")

            name = range_match.group("name")
            start = int(range_match.group("start"))
            end = int(range_match.group("end"))

            for i in range(start, end + 1):
                context = {name: i}
                for inner_key, inner_value in value.items():
                    compiled_key = _compile_range_script(inner_key, context)
                    if isinstance(inner_value, str):
                        compiled_value = _compile_range_script(inner_value, context)
                        parsed_values[compiled_key] = compiled_value
                        continue

                    parsed_inner_values = []
                    for inner_value_item in inner_value:
                        compiled_value = _compile_range_script(
                            inner_value_item, context
                        )
                        parsed_inner_values.append(compiled_value)

                    parsed_values[compiled_key] = parsed_inner_values

        return parsed_values

    async def get_output(self, **raw_inputs: BIT | list[BIT]):
        inputs = self._check_inputs(raw_inputs)

        outputs_to_go = set(self.outputs)
        outputs: dict[str, BIT] = {}

        current_inputs: dict[str, BIT] = {**inputs, **self._output_values}

        assigned_inputs = defaultdict(dict)

        while True:
            for k, v in current_inputs.items():
                wire_ends = self.wires.get(k)

                if wire_ends is None:
                    continue

                if isinstance(wire_ends, str):
                    wire_ends = [wire_ends]

                for wire_end in wire_ends:
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

        self._output_values = outputs

        return outputs

    @property
    def output_values(self):
        return self._output_values

    @property
    def readable_output_values(self):
        outputs = {}
        for key, value in self._output_values.items():
            array_match = array_definition_regex.match(key)

            if array_match is None:
                outputs[key] = value
                continue

            formatted_key = array_match.group("name")
            if formatted_key not in outputs:
                outputs[formatted_key] = []

            index = int(array_match.group("size"))
            outputs[formatted_key].append((index, value))

        outputs = cast(dict[str, BIT | list[tuple[int, BIT]]], outputs)
        formatted_outputs: dict[str, BIT | list[BIT]] = {}

        for key, value in outputs.items():
            if isinstance(value, int):
                formatted_outputs[key] = value
                continue

            size = max([t[0] for t in value]) + 1
            values_list: list[BIT] = [0 for _ in range(size)]
            for t in value:
                values_list[t[0]] = t[1]

            formatted_outputs[key] = values_list

        return formatted_outputs

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
            gate = cls.from_file(path).register()
            logging.info(f"discovered gate {gate.name}")
            gates.append(gate)

        for gate in gates:
            gate.build()

    @classmethod
    def by_name(cls, name: str):
        return cls.__available__[name]


class NotGate(Gate):
    def __init__(self):
        super().__init__(name="not", inputs=["i"], outputs=["o"], gates={}, wires={})
        self.register()

    async def get_output(self, **raw_inputs: BIT | list[BIT]):
        inputs = self._check_inputs(raw_inputs)

        return {"o": 1 - inputs["i"]}


NotGate().register()


class OrGate(Gate):
    def __init__(self):
        super().__init__(
            name="or", inputs=["a", "b"], outputs=["o"], gates={}, wires={}
        )
        self.register()

    async def get_output(self, **raw_inputs: BIT | list[BIT]):
        inputs = self._check_inputs(raw_inputs)

        return {"o": inputs["a"] | inputs["b"]}


OrGate().register()
