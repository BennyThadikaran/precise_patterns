from __future__ import annotations
from typing import Generic, Iterator, Optional, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    """
    A node in a doubly linked list.

    .. attribute:: value
       :type: T

       The value stored in the node.

    .. attribute:: prev
       :type: Optional[:class:`Node`]

       Reference to the previous node, or ``None`` if this is the head.

    .. attribute:: next
       :type: Optional[:class:`Node`]

       Reference to the next node, or ``None`` if this is the tail.
    """

    __slots__ = ("value", "prev", "next")

    def __init__(
        self,
        value: T,
        prev: Optional[Node[T]] = None,
        next: Optional[Node[T]] = None,
    ) -> None:
        """
        Initialize a node.

        :param value: Value to store in the node.
        :type value: T
        :param prev: Previous node.
        :type prev: Optional[:class:`Node`]
        :param next: Next node.
        :type next: Optional[:class:`Node`]
        :returns: ``None``
        :rtype: None
        """
        self.value = value
        self.prev = prev
        self.next = next


class DoublyLinkedList(Generic[T]):
    """
    A generic doubly linked list implementation.

    .. attribute:: _head
       :type: Optional[:class:`Node`]

       The head node of the list.

    .. attribute:: _tail
       :type: Optional[:class:`Node`]

       The tail node of the list.

    .. attribute:: _size
       :type: int

       Number of elements in the list.
    """

    __slots__ = ("_head", "_tail", "_size")

    def __init__(self) -> None:
        """
        Initialize an empty list.

        :returns: ``None``
        :rtype: None
        """
        self._head: Optional[Node[T]] = None
        self._tail: Optional[Node[T]] = None
        self._size: int = 0

    def __len__(self) -> int:
        """
        Return the number of elements in the list.

        :returns: The list size.
        :rtype: int
        """
        return self._size

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over the list from head to tail.

        :returns: An iterator over stored values.
        :rtype: Iterator[T]
        """
        current = self._head
        while current:
            yield current.value
            current = current.next

    def __reversed__(self) -> Iterator[T]:
        """
        Iterate over the list from tail to head.

        :returns: A reverse iterator over stored values.
        :rtype: Iterator[T]
        """
        current = self._tail
        while current:
            yield current.value
            current = current.prev

    def append(self, value: T) -> Node[T]:
        """
        Append a value to the end of the list.

        :param value: Value to append.
        :type value: T
        :returns: The newly created node.
        :rtype: :class:`Node`
        """
        node = Node(value, prev=self._tail)

        if self._tail:
            self._tail.next = node
        else:
            self._head = node

        self._tail = node
        self._size += 1
        return node

    def appendleft(self, value: T) -> Node[T]:
        """
        Append a value to the beginning of the list.

        :param value: Value to append.
        :type value: T
        :returns: The newly created node.
        :rtype: :class:`Node`
        """
        node = Node(value, next=self._head)

        if self._head:
            self._head.prev = node
        else:
            self._tail = node

        self._head = node
        self._size += 1
        return node

    def pop(self) -> T:
        """
        Remove and return the value at the end of the list.

        :returns: The removed value.
        :rtype: T
        :raises IndexError: If the list is empty.
        """
        if not self._tail:
            raise IndexError("pop from empty list")

        value = self._tail.value
        self.remove_node(self._tail)
        return value

    def popleft(self) -> T:
        """
        Remove and return the value at the beginning of the list.

        :returns: The removed value.
        :rtype: T
        :raises IndexError: If the list is empty.
        """
        if not self._head:
            raise IndexError("popleft from empty list")

        value = self._head.value
        self.remove_node(self._head)
        return value

    def insert_after(self, node: Node[T], value: T) -> Node[T]:
        """
        Insert a value after a given node.

        :param node: Node after which to insert.
        :type node: :class:`Node`
        :param value: Value to insert.
        :type value: T
        :returns: The newly created node.
        :rtype: :class:`Node`
        """
        new_node = Node(value, prev=node, next=node.next)

        if node.next:
            node.next.prev = new_node
        else:
            self._tail = new_node

        node.next = new_node
        self._size += 1
        return new_node

    def insert_before(self, node: Node[T], value: T) -> Node[T]:
        """
        Insert a value before a given node.

        :param node: Node before which to insert.
        :type node: :class:`Node`
        :param value: Value to insert.
        :type value: T
        :returns: The newly created node.
        :rtype: :class:`Node`
        """
        new_node = Node(value, prev=node.prev, next=node)

        if node.prev:
            node.prev.next = new_node
        else:
            self._head = new_node

        node.prev = new_node
        self._size += 1
        return new_node

    def remove_node(self, node: Node[T]) -> None:
        """
        Remove a node from the list.

        :param node: Node to remove.
        :type node: :class:`Node`
        :returns: ``None``
        :rtype: None
        """
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
        """
        Remove all elements from the list.

        :returns: ``None``
        :rtype: None
        """
        self._head = None
        self._tail = None
        self._size = 0
