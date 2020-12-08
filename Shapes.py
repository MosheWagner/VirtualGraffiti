from typing import Iterable, Tuple, Optional


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __iter__(self) -> Iterable[int]:
        return iter((self.x, self.y))

    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


class Rectangle:
    def __init__(self, bottom_left: Point, top_right: Point):
        self.bottom_left = bottom_left
        self.top_right = top_right

    def width(self) -> int:
        return self.top_right.x - self.bottom_left.x

    def height(self) -> int:
        return self.top_right.y - self.bottom_left.y

    def left_x(self) -> int:
        return self.bottom_left.x

    def right_x(self) -> int:
        return self.top_right.x

    def top_y(self) -> int:
        return self.top_right.y

    def bottom_y(self) -> int:
        return self.bottom_left.y

    def contains(self, p: Optional[Point]) -> bool:
        if not p:
            return False
        if (
            self.left_x() < p.x < self.right_x()
            and self.bottom_y() < p.y < self.top_y()
        ):
            return True
        return False
