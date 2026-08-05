"""Bytecode representation: a flat, linear sequence of instructions plus a
constant pool, instead of a tree the interpreter re-walks (and re-dispatches
on node type) every time it's evaluated. Not literal packed bytes -- each
instruction is a small (Op, operand) pair -- but the execution model is the
same idea real bytecode VMs use: a single flat array, an instruction
pointer, and a dispatch loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional, Tuple


class Op(Enum):
    CONST = auto()
    POP = auto()

    GET_VAR = auto()
    SET_VAR = auto()
    DEFINE_VAR = auto()

    GET_INDEX = auto()
    SET_INDEX = auto()
    BUILD_LIST = auto()

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()
    NOT = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()

    JUMP = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_FALSE_NO_POP = auto()
    JUMP_IF_TRUE_NO_POP = auto()

    ENTER_SCOPE = auto()
    EXIT_SCOPE = auto()

    MAKE_FUNCTION = auto()
    CALL = auto()
    RETURN = auto()

    BREAK = auto()
    CONTINUE = auto()


Instruction = Tuple[Op, Any]


@dataclass
class Chunk:
    code: List[Instruction] = field(default_factory=list)
    param_names: List[str] = field(default_factory=list)
    name: str = "<script>"

    def emit(self, op: Op, operand: Any = None) -> int:
        self.code.append((op, operand))
        return len(self.code) - 1

    def patch_jump(self, index: int, target: int) -> None:
        op, _ = self.code[index]
        self.code[index] = (op, target)
