from __future__ import annotations
from typing import Sequence

class SourceCodeStack:
    def __init__(self, code: bytes) -> None:
        self.code = bytearray(reversed(code))

    def read_next_token(self) -> bytes:
        return bytes([self.code.pop()])

    def __bool__(self) -> bool:
        return bool(self.code)

class Context:
    def __init__(self, buffer_size: int = 2 ** 16, data: bytes = b"") -> None:
        self.buffer = bytearray(data) + bytearray([0]) * (buffer_size - len(data))
        self.ptr = 0

    @property
    def current_value(self) -> int:
        return self.buffer[self.ptr]

    @current_value.setter
    def current_value(self, value: int):
        # Allow overflow
        self.buffer[self.ptr] = value & 255

    @property
    def pointer(self) -> int:
        return self.ptr

    @pointer.setter
    def pointer(self, value: int):
        # Allow overflow
        self.ptr = value % len(self.buffer)

class Node:
    def exec(self, context: Context) -> None:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return self.__class__.__name__

class CodeBlockNode(Node):
    def __init__(self, child_nodes: Sequence[Node]) -> None:
        self.child_nodes = tuple(child_nodes)

    @classmethod
    def parse(cls, code: SourceCodeStack) -> CodeBlockNode:
        child_nodes = []

        while code:
            token = code.read_next_token()

            if token == b".":
                new_node = PrintNode()

            elif token == b"+":
                new_node = PlusNode()

            elif token == b"-":
                new_node = MinusNode()

            elif token == b">":
                new_node = ForwardNode()

            elif token == b"<":
                new_node = BackwardNode()

            elif token == b"[":
                new_node = WhileNode(CodeBlockNode.parse(code))

            elif token == b"]":
                break
            
            else:
                raise SyntaxError

            child_nodes.append(new_node)

        return CodeBlockNode(child_nodes)

    def exec(self, context: Context) -> None:
        for child_node in self.child_nodes:
            child_node.exec(context)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.child_nodes}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.child_nodes}"

class WhileNode(Node):
    def __init__(self, code_block_node: CodeBlockNode) -> None:
        self.code_block_node = code_block_node

    def exec(self, context: Context) -> None:
        while context.current_value:
            self.code_block_node.exec(context)

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.code_block_node}, )"

class PlusNode(Node):
    def exec(self, context: Context) -> None:
        context.current_value += 1

class MinusNode(Node):
    def exec(self, context: Context) -> None:
        context.current_value -= 1

class ForwardNode(Node):
    def exec(self, context: Context) -> None:
        context.pointer += 1

class BackwardNode(Node):
    def exec(self, context: Context) -> None:
        context.pointer -= 1

class PrintNode(Node):
    def exec(self, context: Context) -> None:
        print(end = chr(context.current_value))

def brainfuck(code: bytes, input_data: bytes = b"", buffer_size: int = 2 ** 16) -> None:
    source_code = SourceCodeStack(code)
    code_block = CodeBlockNode.parse(code = source_code) 

    context = Context(buffer_size = buffer_size, data = input_data)
    code_block.exec(context = context)

if __name__ == "__main__":
    brainfuck(code = b"[.>]", input_data = input().encode())
