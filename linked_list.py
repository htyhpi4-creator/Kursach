from typing import Iterable, Iterator, List, Any, Optional


class Node:
    def __init__(self, data: Any = None):
        self.data = data
        self.next_node: Optional['Node'] = None

    def __repr__(self) -> str:
        return f"Node({self.data!r})"


class LinkedList:
    def __init__(self):
        self.head: Optional[Node] = None
        self._size: int = 0

    def append(self, data: Any) -> None:
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            self._size = 1
            return
        last = self.head
        while last.next_node:
            last = last.next_node
        last.next_node = new_node
        self._size += 1

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        cur = self.head
        while cur:
            yield cur.data
            cur = cur.next_node

    def to_list(self) -> List[Any]:
        return list(self)

    def __str__(self) -> str:
        lines = []
        for i, item in enumerate(self, start=1):
            item_lines = str(item).splitlines()
            if item_lines:
                lines.append(f"{i}. {item_lines[0]}")
                for sub in item_lines[1:]:
                    lines.append(f"    {sub}")
            else:
                lines.append(f"{i}. {str(item)}")
        return "\n".join(lines)

    def _node_at(self, index: int) -> Node:
        if index < 0 or index >= self._size:
            raise IndexError("Індекс виходить за межі списку")
        cur = self.head
        i = 0
        while cur and i < index:
            cur = cur.next_node
            i += 1
        if cur is None:
            raise IndexError("Індекс виходить за межі списку")
        return cur

    def __getitem__(self, index: int) -> Any:
        node = self._node_at(index)
        return node.data

    def __setitem__(self, index: int, value: Any) -> None:
        node = self._node_at(index)
        node.data = value

    def remove(self, index_to_remove: int) -> None:
        if self.head is None:
            raise IndexError("Неможливо видалити з порожнього списку")
        if index_to_remove < 0 or index_to_remove >= self._size:
            raise IndexError("Індекс виходить за межі списку")
        if index_to_remove == 0:
            self.head = self.head.next_node
            self._size -= 1
            return
        prev = self._node_at(index_to_remove - 1)
        node_to_delete = prev.next_node
        if node_to_delete is None:
            raise IndexError("Індекс виходить за межі списку")
        prev.next_node = node_to_delete.next_node
        self._size -= 1

    def __delitem__(self, index: int) -> None:
        self.remove(index)
