"""Native functions available in every Pebble program."""
from __future__ import annotations

import time
from typing import Any, List

from .environment import Environment
from .errors import RuntimeErrorPebble


def install(env: Environment) -> None:
    from .interpreter import NativeFunction, stringify  # avoid circular import at module load

    def _print(interpreter, args: List[Any], line: int) -> None:
        interpreter.output(" ".join(stringify(a) for a in args))
        return None

    def _len(interpreter, args: List[Any], line: int) -> float:
        value = args[0]
        if isinstance(value, (list, str)):
            return float(len(value))
        raise RuntimeErrorPebble("len() expects a list or string.", line)

    def _str(interpreter, args: List[Any], line: int) -> str:
        return stringify(args[0])

    def _num(interpreter, args: List[Any], line: int) -> float:
        value = args[0]
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise RuntimeErrorPebble(f"Cannot convert '{value}' to a number.", line)
        raise RuntimeErrorPebble("num() expects a string or number.", line)

    def _type(interpreter, args: List[Any], line: int) -> str:
        value = args[0]
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        return "function"

    def _range(interpreter, args: List[Any], line: int) -> List[float]:
        nums = [int(a) for a in args]
        if len(nums) == 1:
            return [float(i) for i in range(nums[0])]
        if len(nums) == 2:
            return [float(i) for i in range(nums[0], nums[1])]
        if len(nums) == 3:
            return [float(i) for i in range(nums[0], nums[1], nums[2])]
        raise RuntimeErrorPebble("range() expects 1 to 3 arguments.", line)

    def _push(interpreter, args: List[Any], line: int) -> None:
        target, value = args
        if not isinstance(target, list):
            raise RuntimeErrorPebble("push() expects a list as its first argument.", line)
        target.append(value)
        return None

    def _pop(interpreter, args: List[Any], line: int) -> Any:
        target = args[0]
        if not isinstance(target, list):
            raise RuntimeErrorPebble("pop() expects a list.", line)
        if not target:
            raise RuntimeErrorPebble("pop() on an empty list.", line)
        return target.pop()

    def _clock(interpreter, args: List[Any], line: int) -> float:
        return time.time()

    natives = [
        ("print", None, _print),
        ("len", 1, _len),
        ("str", 1, _str),
        ("num", 1, _num),
        ("type", 1, _type),
        ("range", None, _range),
        ("push", 2, _push),
        ("pop", 1, _pop),
        ("clock", 0, _clock),
    ]
    for name, arity, fn in natives:
        env.define(name, NativeFunction(name, arity, fn))
