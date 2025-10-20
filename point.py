import random
from typing import Optional, List


class MapPoint:
    _instance_counter: int = 0
    _location_names: Optional[List[str]] = None
    _locations_file_missing: bool = False

    def __init__(self, manual_data: Optional[dict] = None):
        self._id = MapPoint._instance_counter
        MapPoint._instance_counter += 1

        if manual_data:
            try:
                lat = float(manual_data.get('lat'))
                lon = float(manual_data.get('lon'))
                lat_hem = str(manual_data.get('lat_hem')).upper()
                lon_hem = str(manual_data.get('lon_hem')).upper()
                loc = str(manual_data.get('location')).strip()
            except (TypeError, ValueError):
                raise ValueError("Некоректні manual_data для MapPoint")

            if lat_hem not in ('N', 'S') or lon_hem not in ('E', 'W'):
                raise ValueError("Півкулі повинні бути 'N'/'S' та 'E'/'W'")

            if not (0.0 <= lat <= 90.0):
                raise ValueError("Широта повинна бути в межах 0..90")
            if not (0.0 <= lon <= 180.0):
                raise ValueError("Довгота повинна бути в межах 0..180")

            self._latitude = round(lat, 4)
            self._latitude_hemisphere = lat_hem
            self._longitude = round(lon, 4)
            self._longitude_hemisphere = lon_hem
            self._location_name = loc if loc else self._get_random_location()
        else:
            self._latitude_hemisphere = random.choice(['N', 'S'])
            self._latitude = round(random.uniform(0, 90), 4)
            self._longitude_hemisphere = random.choice(['E', 'W'])
            self._longitude = round(random.uniform(0, 180), 4)
            self._location_name = self._get_random_location()

        self._recalculate_surface()

    def _get_random_location(self) -> str:
        if MapPoint._locations_file_missing:
            return "Невідоме місце (файл locations.txt не знайдено)"

        if MapPoint._location_names is None:
            try:
                with open('locations.txt', 'r', encoding='utf-8') as f:
                    MapPoint._location_names = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                MapPoint._location_names = []
                MapPoint._locations_file_missing = True
                return "Невідоме місце (файл locations.txt не знайдено)"

        if not MapPoint._location_names:
            return "Невідоме місце (файл locations.txt порожній)"
        return random.choice(MapPoint._location_names)

    def _recalculate_surface(self) -> None:
        name = (self._location_name or "").lower()

        ocean_keys = ['ocean', 'sea', 'океан', 'море', 'морський', 'моря', 'атлантичний', 'тихий', 'індійський']
        lake_keys = ['lake', 'озеро', 'озер', 'байкал']
        island_keys = ['island', 'острів', 'isla', 'insula', 'мадагаскар']

        if any(k in name for k in ocean_keys):
            self._surface = 'океан'
        elif any(k in name for k in lake_keys):
            self._surface = 'озеро'
        elif any(k in name for k in island_keys):
            self._surface = 'острів'
        else:
            self._surface = 'материк'

    def update_coordinates(self, lat: float, lat_hem: str, lon: float, lon_hem: str) -> None:
        lat_hem = str(lat_hem).upper()
        lon_hem = str(lon_hem).upper()
        if lat_hem not in ('N', 'S') or lon_hem not in ('E', 'W'):
            raise ValueError("Півкулі повинні бути 'N'/'S' і 'E'/'W'")
        if not (0.0 <= float(lat) <= 90.0):
            raise ValueError("Широта повинна бути в межах 0..90")
        if not (0.0 <= float(lon) <= 180.0):
            raise ValueError("Довгота повинна бути в межах 0..180")

        self._latitude = round(float(lat), 4)
        self._latitude_hemisphere = lat_hem
        self._longitude = round(float(lon), 4)
        self._longitude_hemisphere = lon_hem
        self._recalculate_surface()

    def set_location_name(self, new_name: str) -> None:
        self._location_name = str(new_name).strip()
        self._recalculate_surface()

    def __str__(self) -> str:
        return (f"ID: {self._id}\n"
                f"Координати: {self._latitude}°{self._latitude_hemisphere}, {self._longitude}°{self._longitude_hemisphere}\n"
                f"Місце: {self._location_name}\n"
                f"Тип поверхні: {self._surface}")

    def __repr__(self) -> str:
        return f"MapPoint(id={self._id}, loc={self._location_name!r}, surface={self._surface!r})"

    @property
    def id(self) -> int:
        return self._id

    @property
    def location_name(self) -> str:
        return self._location_name

    @property
    def surface(self) -> str:
        return self._surface

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def latitude_hemisphere(self) -> str:
        return self._latitude_hemisphere

    @property
    def longitude_hemisphere(self) -> str:
        return self._longitude_hemisphere

    @staticmethod
    def get_instance_count() -> int:
        return MapPoint._instance_counter

    @staticmethod
    def reset_instance_counter() -> None:
        MapPoint._instance_counter = 0

    @staticmethod
    def get_land_percentage_from_list(points_list) -> float:
        pts = list(points_list)
        total = len(pts)
        if total == 0:
            return 0.0
        land = sum(1 for p in pts if getattr(p, 'surface', '').lower() in ('материк', 'острів'))
        return (land / total) * 100.0
