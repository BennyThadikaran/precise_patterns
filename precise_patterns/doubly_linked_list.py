from __future__ import annotations
from typing import Generic, Iterator, Optional, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    __slots__ = ("value", "prev", "next")

    def __init__(
        self,
        value: T,
        prev: Optional[Node[T]] = None,
        next: Optional[Node[T]] = None,
    ) -> None:
        self.value = value
        self.prev = prev
        self.next = next


class DoublyLinkedList(Generic[T]):
    __slots__ = ("_head", "_tail", "_size")

    def __init__(self) -> None:
        self._head: Optional[Node[T]] = None
        self._tail: Optional[Node[T]] = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        current = self._head
        while current:
            yield current.value
            current = current.next

    def __reversed__(self) -> Iterator[T]:
        current = self._tail
        while current:
            yield current.value
            current = current.prev

    def append(self, value: T) -> Node[T]:
        node = Node(value, prev=self._tail)
        if self._tail:
            self._tail.next = node
        else:
            self._head = node
        self._tail = node
        self._size += 1
        return node

    def appendleft(self, value: T) -> Node[T]:
        node = Node(value, next=self._head)
        if self._head:
            self._head.prev = node
        else:
            self._tail = node
        self._head = node
        self._size += 1
        return node

    def pop(self) -> T:
        if not self._tail:
            raise IndexError("pop from empty list")
        value = self._tail.value
        self.remove_node(self._tail)
        return value

    def popleft(self) -> T:
        if not self._head:
            raise IndexError("popleft from empty list")
        value = self._head.value
        self.remove_node(self._head)
        return value

    def insert_after(self, node: Node[T], value: T) -> Node[T]:
        new_node = Node(value, prev=node, next=node.next)

        if node.next:
            node.next.prev = new_node
        else:
            self._tail = new_node

        node.next = new_node
        self._size += 1
        return new_node

    def insert_before(self, node: Node[T], value: T) -> Node[T]:
        new_node = Node(value, prev=node.prev, next=node)

        if node.prev:
            node.prev.next = new_node
        else:
            self._head = new_node

        node.prev = new_node
        self._size += 1
        return new_node

    def remove_node(self, node: Node[T]) -> None:
        if node.prev:
            node.prev.next = node.next
        else:
            self._head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            self._tail = node.prev

        node.prev = None
        node.next = None
        self._size -= 1

    def clear(self) -> None:
        self._head = None
        self._tail = None
        self._size = 0
