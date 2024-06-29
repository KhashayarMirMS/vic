import asyncio
import glob
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal, cast
from pydantic import BaseModel, PrivateAttr, field_validator
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


class Pin:
    _value: BIT
    _listeners: list[Callable[[], Awaitable[None]]]

    def __init__(self):
        self._value = 0
        self._listeners = []

    @property
    def value(self):
        return self._value

    async def set_value(self, new_value: BIT):
        self._value = new_value

        await asyncio.gather(*[listener() for listener in self._listeners])

    def add_listener(self, listener: Callable[[], Awaitable[None]]):
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], Awaitable[None]]):
        self._listeners.remove(listener)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return str(self._value)


class Wire:
    _input_pin: Pin
    _output_pin: Pin

    def __init__(self, input_pin: Pin, output_pin: Pin):
        self._input_pin = input_pin
        self._output_pin = output_pin

        self._input_pin.add_listener(self.listener)

    async def initialize(self):
        await self._output_pin.set_value(self._input_pin.value)

    async def listener(self):
        if self._output_pin.value == self._input_pin.value:
            return

        await self._output_pin.set_value(self._input_pin.value)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self._input_pin}--{self._output_pin}"


class Gate(BaseModel):
    name: str
    inputs: list[str]
    outputs: list[str]
    gates: dict[str, str]
    wires: dict[str, str | list[str]]
    _built_gates: dict[str, "Gate"] = PrivateAttr(default_factory=dict)
    _input_pins: dict[str, Pin] = PrivateAttr(default_factory=dict)
    _output_pins: dict[str, Pin] = PrivateAttr(default_factory=dict)
    _wires: list[Wire] = PrivateAttr(default_factory=list)

    __available__: dict[str, "Gate"] = {}

    def __init__(self, /, **data):
        if data["name"] == "32b-adder":
            print(data)
        super().__init__(**data)

    def register(self):
        if self.name not in Gate.__available__:
            Gate.__available__[self.name] = self

        return self

    async def build(self):
        # if self.name == '32b-full-adder':
        #     print(self.gates.items())
        for gate_name, gate_type in self.gates.items():
            self._built_gates[gate_name] = await Gate.by_name(gate_type)

        for input_name in self.inputs:
            self._input_pins[input_name] = Pin()

        for output_name in self.outputs:
            self._output_pins[output_name] = Pin()

        # if self.name == '32b-full-adder':
        #     print(self._built_gates.keys())
        for start_pin_name, end_pin_names in self.wires.items():
            if isinstance(end_pin_names, str):
                end_pin_names = [end_pin_names]

            for end_pin_name in end_pin_names:
                if "." in start_pin_name:
                    gate_name, pin_name = start_pin_name.split(".")
                    start_pin = self._built_gates[gate_name].pins[pin_name]
                else:
                    start_pin = self.pins[start_pin_name]

                if "." in end_pin_name:
                    gate_name, pin_name = end_pin_name.split(".")
                    end_pin = self._built_gates[gate_name].pins[pin_name]
                else:
                    end_pin = self.pins[end_pin_name]

                wire = Wire(start_pin, end_pin)
                await wire.initialize()
                self._wires.append(wire)

        return self

    @property
    def pins(self):
        return {**self._input_pins, **self._output_pins}

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

        return inputs

    async def get_output(self, **raw_inputs: BIT | list[BIT]):
        inputs = self._check_inputs(raw_inputs)

        await asyncio.gather(
            *[self._input_pins[name].set_value(bit) for name, bit in inputs.items()]
        )

        return self.output_values

    @property
    def output_values(self) -> dict[str, BIT]:
        return {name: pin.value for name, pin in self._output_pins.items()}

    @property
    def readable_output_values(self):
        outputs = {}
        for key, value in self.output_values.items():
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
                values_list[t[0]] = cast(BIT, t[1])

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
    async def discover(cls, base_dir: str | Path):
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

    @classmethod
    async def by_name(cls, name: str):
        template_gate = cls.__available__[name].model_copy(deep=True)
        return await template_gate.build()


class NotGate(Gate):
    def __init__(self):
        super().__init__(name="not", inputs=["i"], outputs=["o"], gates={}, wires={})

    async def build(self):
        await super().build()
        self._input_pins["i"].add_listener(self.listener)

        return self

    async def listener(self):
        await self._output_pins["o"].set_value(1 - self._input_pins["i"].value)

    def model_dump(self, *_, **__):
        return {}


NotGate().register()


class OrGate(Gate):
    def __init__(self):
        super().__init__(
            name="or", inputs=["a", "b"], outputs=["o"], gates={}, wires={}
        )

    async def build(self):
        await super().build()
        self._input_pins["a"].add_listener(self.listener)
        self._input_pins["b"].add_listener(self.listener)

        return self

    async def listener(self):
        await self._output_pins["o"].set_value(
            cast(BIT, self._input_pins["a"].value | self._input_pins["b"].value)
        )

    def model_dump(self, *_, **__):
        return {}


OrGate().register()
