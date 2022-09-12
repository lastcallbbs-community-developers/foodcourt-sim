#!/usr/bin/env python3
import io
import struct
from typing import Any, Union

from .enums import LevelId, ModuleId, MusicMode, PaintColor, PaintMask
from .errors import InvalidSolutionError
from .levels import BY_ID, Level
from .models import Direction, Position, Solution, Wire
from .modules import (
    MODULE_LOOKUP,
    Animatronic,
    BigCounter,
    Input,
    Module,
    Painter,
    Sequencer,
    SmallCounter,
)


def read_bytes(stream: io.BufferedIOBase, size: int) -> bytes:
    b = stream.read(size)
    assert (
        len(b) == size
    ), f"could not read enough bytes (requested: {size}, got: {len(b)})"
    return b


def write_bytes(stream: io.BufferedIOBase, b: bytes) -> None:
    stream.write(b)


def read_int(stream: io.BufferedIOBase, size: int) -> int:
    return int.from_bytes(read_bytes(stream, size), byteorder="little", signed=True)


def write_int(stream: io.BufferedIOBase, value: int, size: int) -> None:
    stream.write(value.to_bytes(size, byteorder="little", signed=True))


def read_bool(stream: io.BufferedIOBase) -> bool:
    x = read_bytes(stream, 1)[0]
    assert x in [0, 1], f"invalid bool value {x:#x}"
    return x == 1


def write_bool(stream: io.BufferedIOBase, b: bool) -> None:
    stream.write(b.to_bytes(1, byteorder="little"))


def read_string(stream: io.BufferedIOBase) -> str:
    size = read_int(stream, 4)
    return read_bytes(stream, size).decode()


def write_string(stream: io.BufferedIOBase, s: str) -> None:
    write_int(stream, len(s), 4)
    write_bytes(stream, s.encode())


def read_position(stream: io.BufferedIOBase) -> Position:
    column = read_int(stream, 4)
    row = read_int(stream, 4)
    return Position(column, row)


def write_position(stream: io.BufferedIOBase, pos: Position) -> None:
    write_int(stream, pos.column, 4)
    write_int(stream, pos.row, 4)


def read_module(stream: io.BufferedIOBase, level: Level) -> Module:
    module_id = ModuleId(read_int(stream, 4))
    cls = MODULE_LOOKUP[module_id]
    can_delete = read_bool(stream)
    rack_pos = read_position(stream)
    floor_pos = read_position(stream)
    # pylint: disable-next=protected-access
    extras: dict[str, Any] = {}
    if issubclass(cls, Input):
        extras["input_id"] = read_int(stream, 4)
    elif issubclass(cls, SmallCounter):
        extras["values"] = [read_int(stream, 4) for _ in range(2)]
    elif issubclass(cls, BigCounter):
        extras["values"] = [read_int(stream, 4) for _ in range(4)]
    elif issubclass(cls, Sequencer):
        data = read_bytes(stream, 4 * 12)
        extras["rows"] = list(map(list, struct.iter_unpack("4?", data)))
    elif issubclass(cls, Painter):
        extras["color"] = PaintColor(read_int(stream, 4))
        extras["mask"] = PaintMask(read_int(stream, 4))
    elif issubclass(cls, Animatronic):
        extras["music_mode"] = MusicMode(read_int(stream, 1))

    direction = Direction(read_int(stream, 1))

    return cls(level, module_id, can_delete, rack_pos, floor_pos, direction, **extras)


def write_module(stream: io.BufferedIOBase, module: Module) -> None:
    write_int(stream, module.id.value, 4)
    write_bool(stream, module.can_delete)
    write_position(stream, module.rack_position)
    write_position(stream, module.floor_position)
    if isinstance(module, Input):
        write_int(stream, module.input_id, 4)
    elif isinstance(module, (SmallCounter, BigCounter)):
        for val in module.values:
            write_int(stream, val, 4)
    elif isinstance(module, Sequencer):
        for row in module.rows:
            write_bytes(stream, struct.pack("4?", *row))
    elif isinstance(module, Painter):
        write_int(stream, module.color.value, 4)
        write_int(stream, module.mask.value, 4)
    elif isinstance(module, Animatronic):
        write_int(stream, module.music_mode.value, 1)
    write_int(stream, module.direction.value, 1)


def read_wire(stream: io.BufferedIOBase) -> Wire:
    module_1 = read_int(stream, 4)
    jack_1 = read_int(stream, 4)
    module_2 = read_int(stream, 4)
    jack_2 = read_int(stream, 4)
    return Wire(module_1, jack_1, module_2, jack_2)


def write_wire(stream: io.BufferedIOBase, wire: Wire) -> None:
    write_int(stream, wire.module_1, 4)
    write_int(stream, wire.jack_1, 4)
    write_int(stream, wire.module_2, 4)
    write_int(stream, wire.jack_2, 4)


def read_solution(data: Union[bytes, io.BufferedIOBase]) -> Solution:
    if isinstance(data, io.BufferedIOBase):
        stream = data
    else:
        stream = io.BytesIO(data)
    version = read_int(stream, 4)
    if not 1000 <= version <= 1013:
        raise InvalidSolutionError(
            f"invalid solution version {version} (must be between 1000 and 1013)"
        )

    level_id = LevelId(read_int(stream, 4))
    name = read_string(stream)

    solved = read_bool(stream)
    time = read_int(stream, 4)
    cost = read_int(stream, 4)

    level = BY_ID[level_id]
    num_modules = read_int(stream, 4)
    modules = [read_module(stream, level) for _ in range(num_modules)]

    num_wires = read_int(stream, 4)
    wires = [read_wire(stream) for _ in range(num_wires)]

    solution = Solution(version, level_id, name, solved, time, cost, modules, wires)
    return solution


def write_solution(stream: io.BufferedIOBase, solution: Solution) -> None:
    write_int(stream, solution.version, 4)
    write_int(stream, solution.level_id.value, 4)
    write_string(stream, solution.name)
    write_bool(stream, solution.solved)
    write_int(stream, solution.time, 4)
    write_int(stream, solution.cost, 4)
    write_int(stream, len(solution.modules), 4)
    for module in solution.modules:
        write_module(stream, module)
    write_int(stream, len(solution.wires), 4)
    for wire in solution.wires:
        write_wire(stream, wire)
