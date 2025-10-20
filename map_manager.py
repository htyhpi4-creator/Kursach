from point import MapPoint
from linked_list import LinkedList
from typing import Optional, List

MAX_POINTS = 30

class MapManager:
    def __init__(self):
        self._points = LinkedList()

    def fill_random_points(self, count: int = 10, reset_ids: bool = False) -> int:
        if count > MAX_POINTS:
            count = MAX_POINTS
        if reset_ids:
            MapPoint.reset_instance_counter()
        self._points = LinkedList()
        created = 0
        for _ in range(count):
            if len(self._points) >= MAX_POINTS:
                break
            self._points.append(MapPoint())
            created += 1
        return created

    def append_point(self, point: MapPoint) -> None:
        if len(self._points) >= MAX_POINTS:
            raise ValueError(f"Нельзя добавить более {MAX_POINTS} точек")
        self._points.append(point)

    def add_point(self, manual_data: Optional[dict] = None) -> MapPoint:
        if len(self._points) >= MAX_POINTS:
            raise ValueError(f"Нельзя добавить более {MAX_POINTS} точек")
        p = MapPoint(manual_data)
        self._points.append(p)
        return p

    def remove_point_by_id(self, point_id: int) -> bool:
        idx = -1
        for i, p in enumerate(self._points):
            if p.id == point_id:
                idx = i
                break
        if idx == -1:
            return False
        self._points.remove(idx)
        return True

    def remove_point_by_index(self, index: int) -> None:
        self._points.remove(index)

    def get_point_by_id(self, point_id: int):
        for p in self._points:
            if p.id == point_id:
                return p
        return None

    def get_point_by_index(self, index: int):
        try:
            return self._points[index]
        except IndexError:
            return None

    def get_all_points(self) -> LinkedList:
        return self._points

    def get_all_points_list(self) -> List[MapPoint]:
        return self._points.to_list()

    def to_list(self) -> List[MapPoint]:
        return self.get_all_points_list()

    def get_order_number(self, point_id: int):
        for idx, p in enumerate(self._points):
            if p.id == point_id:
                return idx + 1
        return None

    def sort_by_location_name(self) -> None:
        if len(self._points) < 2:
            return
        temp = self._points.to_list()
        temp.sort(key=lambda p: p.location_name)
        new_ll = LinkedList()
        for p in temp:
            new_ll.append(p)
        self._points = new_ll

    def filter_by(self, key: str, value: str):
        key = key.lower()
        res = []
        if key == 'surface':
            v = value.strip().lower()
            res = [p for p in self._points if getattr(p, 'surface', '').lower() == v]
        elif key == 'hem_lat':
            v = value.strip().upper()
            if v in ('N', 'S'):
                res = [p for p in self._points if getattr(p, 'latitude_hemisphere', '') == v]
        elif key == 'hem_lon':
            v = value.strip().upper()
            if v in ('E', 'W'):
                res = [p for p in self._points if getattr(p, 'longitude_hemisphere', '') == v]
        return res

    def get_active_count(self) -> int:
        return len(self._points)
