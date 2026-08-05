"""Executes a compiled Chunk directly, instead of recursively walking the
AST and re-dispatching on node type at every single node like interpreter.py
does. Variable scoping still goes through the same Environment chain the
tree-walker uses (see compiler.py's docstring for why), so this is a
narrower change than it might sound: same scoping/closure semantics, same
runtime values, different execution strategy for the flow of control.

One genuine, testable side effect of not using Python recursion for Pebble
function calls (a real Python call stack frame per nested tree-walking
call vs. one flat `while` loop here, with Pebble call frames pushed onto
a plain list): Pebble-level recursion depth is no longer bounded by
Python's own recursion limit. See test_vm.py::
test_vm_handles_deeper_recursion_than_the_tree_walking_interpreter.
"""
from __future__ import annotations

from typing import Any, List, Optional

from .bytecode import Chunk, Op
from .environment import Environment
from .errors import RuntimeErrorPebble
from .interpreter import NativeFunction, is_truthy


class BytecodeFunction:
    def __init__(self, chunk: Chunk, closure_env: Environment):
        self.chunk = chunk
        self.closure_env = closure_env

    def __repr__(self) -> str:
        return f"<fn {self.chunk.name}>"


class _Frame:
    __slots__ = ("chunk", "ip", "env")

    def __init__(self, chunk: Chunk, ip: int, env: Environment):
        self.chunk = chunk
        self.ip = ip
        self.env = env


def _index_get(collection: Any, index: Any, line: int) -> Any:
    if isinstance(collection, (list, str)):
        if not isinstance(index, float) or not index.is_integer():
            raise RuntimeErrorPebble("Index must be an integer.", line)
        i = int(index)
        if not (-len(collection) <= i < len(collection)):
            raise RuntimeErrorPebble("Index out of range.", line)
        return collection[i]
    raise RuntimeErrorPebble("Only lists and strings can be indexed.", line)


def _index_set(collection: Any, index: Any, value: Any, line: int) -> None:
    if not isinstance(collection, list):
        raise RuntimeErrorPebble("Only lists support index assignment.", line)
    if not isinstance(index, float) or not index.is_integer():
        raise RuntimeErrorPebble("Index must be an integer.", line)
    i = int(index)
    if not (-len(collection) <= i < len(collection)):
        raise RuntimeErrorPebble("Index out of range.", line)
    collection[i] = value


def _binary_op(op: Op, left: Any, right: Any, line: int) -> Any:
    if op == Op.ADD:
        if isinstance(left, float) and isinstance(right, float):
            return left + right
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        if isinstance(left, list) and isinstance(right, list):
            return left + right
        raise RuntimeErrorPebble(
            "Operands of '+' must both be numbers, both strings, or both lists.", line
        )

    if op in (Op.SUB, Op.MUL, Op.DIV, Op.MOD):
        if not isinstance(left, float) or not isinstance(right, float):
            raise RuntimeErrorPebble("Operands must be numbers.", line)
        if op == Op.SUB:
            return left - right
        if op == Op.MUL:
            return left * right
        if right == 0:
            raise RuntimeErrorPebble("Division by zero.", line)
        return left / right if op == Op.DIV else left % right

    if op in (Op.LT, Op.LE, Op.GT, Op.GE):
        both_numbers = isinstance(left, float) and isinstance(right, float)
        both_strings = isinstance(left, str) and isinstance(right, str)
        if not (both_numbers or both_strings):
            raise RuntimeErrorPebble(
                "Operands for comparison must both be numbers or both strings.", line
            )
        if op == Op.LT:
            return left < right
        if op == Op.LE:
            return left <= right
        if op == Op.GT:
            return left > right
        return left >= right

    if op == Op.EQ:
        return left == right
    return left != right  # Op.NEQ


class VM:
    def __init__(self, output=print):
        self.output = output
        self.globals = Environment()
        from . import builtins as pebble_builtins

        pebble_builtins.install(self.globals)

    def run(self, chunk: Chunk) -> None:
        self._execute(chunk, self.globals)

    def _execute(self, chunk: Chunk, env: Environment) -> Optional[Any]:
        stack: List[Any] = []
        frames: List[_Frame] = [_Frame(chunk, 0, env)]

        while True:
            frame = frames[-1]
            if frame.ip >= len(frame.chunk.code):
                if len(frames) == 1:
                    return None  # top-level script chunk fell off the end
                frames.pop()
                stack.append(None)
                continue

            op, operand = frame.chunk.code[frame.ip]
            frame.ip += 1

            # Ordered by measured hit frequency on a recursive-call-heavy
            # benchmark (fib), not alphabetically or by category -- Python's
            # if/elif chain is a linear scan, so a naive top-to-bottom
            # opcode listing here made the VM *slower* than the tree-walking
            # interpreter it was meant to beat (profiling showed the bulk of
            # execution time was the dispatch chain itself, not any one
            # opcode's handler). See the README for the full story.
            if op == Op.GET_VAR:
                name, line = operand
                stack.append(frame.env.get(name, line))
            elif op == Op.CONST:
                stack.append(operand)
            elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.LT, Op.LE, Op.GT, Op.GE):
                right = stack.pop()
                left = stack.pop()
                stack.append(_binary_op(op, left, right, operand))
            elif op == Op.CALL:
                argc, line = operand
                args = stack[len(stack) - argc :] if argc else []
                if argc:
                    del stack[len(stack) - argc :]
                callee = stack.pop()

                if isinstance(callee, BytecodeFunction):
                    expected = len(callee.chunk.param_names)
                    if expected != argc:
                        raise RuntimeErrorPebble(
                            f"Expected {expected} argument(s) but got {argc}.", line
                        )
                    call_env = Environment(callee.closure_env)
                    for pname, arg in zip(callee.chunk.param_names, args):
                        call_env.define(pname, arg)
                    frames.append(_Frame(callee.chunk, 0, call_env))
                elif isinstance(callee, NativeFunction):
                    arity = callee.arity()
                    if arity is not None and len(args) != arity:
                        raise RuntimeErrorPebble(
                            f"Expected {arity} argument(s) but got {len(args)}.", line
                        )
                    stack.append(callee.call(self, args, line))
                else:
                    raise RuntimeErrorPebble("Can only call functions.", line)
            elif op == Op.RETURN:
                value = stack.pop()
                frames.pop()
                if not frames:
                    return value
                stack.append(value)
            elif op == Op.JUMP_IF_FALSE:
                if not is_truthy(stack.pop()):
                    frame.ip = operand
            elif op == Op.POP:
                stack.pop()
            elif op == Op.JUMP or op == Op.BREAK or op == Op.CONTINUE:
                frame.ip = operand
            elif op == Op.SET_VAR:
                name, line = operand
                frame.env.assign(name, stack[-1], line)
            elif op == Op.DEFINE_VAR:
                frame.env.define(operand, stack.pop())
            elif op == Op.ENTER_SCOPE:
                frame.env = Environment(frame.env)
            elif op == Op.EXIT_SCOPE:
                frame.env = frame.env.parent
            elif op == Op.EQ:
                right, left = stack.pop(), stack.pop()
                stack.append(left == right)
            elif op == Op.NEQ:
                right, left = stack.pop(), stack.pop()
                stack.append(left != right)
            elif op == Op.GET_INDEX:
                index = stack.pop()
                collection = stack.pop()
                stack.append(_index_get(collection, index, operand))
            elif op == Op.SET_INDEX:
                value = stack.pop()
                index = stack.pop()
                collection = stack.pop()
                _index_set(collection, index, value, operand)
                stack.append(value)
            elif op == Op.BUILD_LIST:
                n = operand
                items = stack[len(stack) - n :] if n else []
                if n:
                    del stack[len(stack) - n :]
                stack.append(list(items))
            elif op == Op.NEG:
                value = stack.pop()
                if not isinstance(value, float):
                    raise RuntimeErrorPebble("Operand of '-' must be a number.", operand)
                stack.append(-value)
            elif op == Op.NOT:
                stack.append(not is_truthy(stack.pop()))
            elif op == Op.JUMP_IF_FALSE_NO_POP:
                if not is_truthy(stack[-1]):
                    frame.ip = operand
            elif op == Op.JUMP_IF_TRUE_NO_POP:
                if is_truthy(stack[-1]):
                    frame.ip = operand
            elif op == Op.MAKE_FUNCTION:
                stack.append(BytecodeFunction(operand, frame.env))
            else:
                raise RuntimeError(f"unknown opcode {op!r}")
