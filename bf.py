from __future__ import annotations
import sys
from typing import Sequence, TextIO, BinaryIO


class SourceCodeStack:
    def __init__(self, code: bytes) -> None:
        self.code = bytearray(reversed(code))

    def read_next_token(self) -> bytes:
        return bytes([self.code.pop()])

    def __bool__(self) -> bool:
        return bool(self.code)

class Context:
    def __init__(self, 
            input_file:  TextIO | BinaryIO | None = sys.stdin, 
            output_file: TextIO | BinaryIO = sys.stdout,
            buffer_size: int = 2 ** 16,
            num_cycles_limit: int = 2 ** 24) -> None:
            
        self.buffer = bytearray([0]) * buffer_size
        self.ptr = 0

        self.input_file = input_file
        self.output_file = output_file

        self.num_cycles_left = num_cycles_limit

    def exec(self, node: Node):
        if self.num_cycles_left == 0:
            raise TimeoutError

        self.num_cycles_left -= 1
        node.exec(self)

    def read(self, n: int = -1, /) -> bytes:
        if self.input_file is None:
            return b""

        if isinstance(self.input_file, BinaryIO):
            return self.input_file.read(n)

        return bytes(map(ord,self.input_file.read(n)))

    def write(self, bytes_: bytes, /) -> None:
        from io import TextIOWrapper, StringIO

        # TODO XXX
        if ( isinstance(self.output_file, TextIO) or
             isinstance(self.output_file, TextIOWrapper) or
             isinstance(self.output_file, StringIO)):
            
            string_ = "".join(map(chr,bytes_))
            self.output_file.write(string_)

        else:
            self.output_file.write(bytes_)

        self.output_file.flush()
        
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
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

class CodeBlockNode(Node):
    def __init__(self, child_nodes: Sequence[Node]) -> None:
        self.child_nodes = tuple(child_nodes)

    @classmethod
    def parse(cls, code: SourceCodeStack) -> CodeBlockNode:
        child_nodes = []

        while code:
            token = code.read_next_token()

            if   token == b".":
                new_node = PrintNode()

            elif token == b",":
                new_node = ReadNode()

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
            context.exec(child_node)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.child_nodes}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.child_nodes}"

class WhileNode(Node):
    def __init__(self, code_block_node: CodeBlockNode) -> None:
        self.code_block_node = code_block_node

    def exec(self, context: Context) -> None:
        while context.current_value:
            context.exec(self.code_block_node)

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
        context.write(bytes([context.current_value]))

class ReadNode(Node):
    def exec(self, context: Context) -> None:
        context.current_value = ord(context.read(1) or b"\0")

def brainfuck(code:  bytes, 
        input_file:  TextIO | BinaryIO | None = sys.stdin,
        output_file: TextIO | BinaryIO = sys.stdout,
        buffer_size: int = 2 ** 16, num_cycles_limit: int = 2 ** 24):

    
    context = Context(input_file = input_file, output_file = output_file, buffer_size = buffer_size, num_cycles_limit = num_cycles_limit)

    source_code = SourceCodeStack(code)
    code_block = CodeBlockNode.parse(code = source_code) 

    context.exec(code_block)

if __name__ == "__main__":
    brainfuck(code = b"+[>,.]")
