"""Самоварный аэростат «Пыхтун», реализация SPEC.md v0.3."""

import math


class CrazyVehicleError(Exception):
    """Базовая ошибка безумного транспорта."""


class SamovarError(CrazyVehicleError):
    """Базовая ошибка самоварного аэростата."""


class SamovarCannotSwim(SamovarError):
    """Вода гасит топку."""


class SamovarBalloonTorn(SamovarError):
    """Порванная оболочка не позволяет лететь."""


class SamovarTooHeavy(SamovarError):
    """Масса превышает грузоподъёмность."""


class SamovarOutOfSteam(SamovarError):
    """Недостаточно пара; required и available доступны вызывающему."""

    def __init__(self, required: float, available: float) -> None:
        self.required = float(required)
        self.available = float(available)
        super().__init__(
            f"not enough steam: required {self.required:g}, "
            f"have {self.available:g}"
        )


def _check_number_type(value: float, parameter: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{parameter} must be a number")


def _finite_number(value: float, parameter: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{parameter} must be finite")
    return number


def _positive_number(value: float, parameter: str) -> float:
    number = _finite_number(value, parameter)
    if number <= 0:
        raise ValueError(f"{parameter} must be positive")
    return number


class SamovarBalloon:
    """Летает, ходит по земле и расходует пар на движение и чай."""

    def __init__(
        self,
        name: str,
        mass_kg: float,
        balloon_volume_m3: float,
        max_speed_kmh: float,
        steam: float = 100.0,
    ) -> None:
        # SPEC 3.0: сначала все типы, затем значения.
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        for parameter, value in (
            ("mass_kg", mass_kg), ("balloon_volume_m3", balloon_volume_m3),
            ("max_speed_kmh", max_speed_kmh), ("steam", steam),
        ):
            _check_number_type(value, parameter)
        if not name.strip():
            raise ValueError("name must not be empty")
        self._name = name
        self._mass_kg = _positive_number(mass_kg, "mass_kg")
        self._balloon_volume_m3 = _positive_number(
            balloon_volume_m3, "balloon_volume_m3"
        )
        self._max_speed_kmh = _positive_number(max_speed_kmh, "max_speed_kmh")
        steam = _finite_number(steam, "steam")
        if not 0 <= steam <= 100:
            raise ValueError("steam must be between 0 and 100")
        self._steam = steam
        self._position_km = 0.0
        self._is_flying = False
        self._balloon_intact = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def mass_kg(self) -> float:
        return self._mass_kg

    @property
    def balloon_volume_m3(self) -> float:
        return self._balloon_volume_m3

    @property
    def max_speed_kmh(self) -> float:
        return self._max_speed_kmh

    @property
    def steam(self) -> float:
        return self._steam

    @property
    def position_km(self) -> float:
        return self._position_km

    @property
    def is_flying(self) -> bool:
        return self._is_flying

    @property
    def balloon_intact(self) -> bool:
        return self._balloon_intact

    @property
    def lift_capacity_kg(self) -> float:
        return self.balloon_volume_m3 * 0.25

    @property
    def can_fly(self) -> bool:
        return (
            self.balloon_intact
            and self.mass_kg <= self.lift_capacity_kg
            and self.steam > 0
        )

    def calculate_steam(self, distance_km: float, terrain: str) -> float:
        """Рассчитать расход без проверки возможности полёта и запаса."""
        _check_number_type(distance_km, "distance_km")
        if not isinstance(terrain, str):
            raise TypeError("terrain must be a string")
        distance = _positive_number(distance_km, "distance_km")
        if terrain not in ("air", "ground", "water"):
            raise ValueError(f"unknown terrain: {terrain}")
        if terrain == "water":
            raise SamovarCannotSwim("samovar cannot swim: water puts out the fire")
        return distance * (2.0 if terrain == "air" else 3.0)

    def move(self, distance_km: float, terrain: str) -> float:
        """Пройти участок целиком; при ошибке состояние сохраняется."""
        required = self.calculate_steam(distance_km, terrain)
        if terrain == "air":
            if not self.balloon_intact:
                raise SamovarBalloonTorn("balloon is torn")
            if self.mass_kg > self.lift_capacity_kg:
                raise SamovarTooHeavy(
                    f"too heavy to fly: mass {self.mass_kg:g} kg, "
                    f"lift {self.lift_capacity_kg:g} kg"
                )
        self._check_steam(required)
        distance = float(distance_km)
        speed = self.max_speed_kmh * (1.0 if terrain == "air" else 0.25)
        hours = distance / speed
        self._steam -= required
        self._position_km += distance
        self._is_flying = terrain == "air"
        return hours

    def _check_steam(self, required: float) -> None:
        if required > self.steam:
            raise SamovarOutOfSteam(required, self.steam)

    def can_overcome(self, obstacle: str) -> bool:
        """Проверить препятствие без движения и расхода пара."""
        if not isinstance(obstacle, str):
            raise TypeError("obstacle must be a string")
        if obstacle == "wall":
            return self.is_flying
        if obstacle == "river":
            return self.can_fly
        if obstacle == "low_bridge":
            return not self.is_flying
        raise ValueError(f"unknown obstacle: {obstacle}")

    def add_coal(self, amount: float) -> None:
        """Пополнить запас пара, не превышая 100 единиц."""
        _check_number_type(amount, "amount")
        amount = _positive_number(amount, "amount")
        self._steam = min(100.0, self.steam + amount)

    def brew_tea(self, cups: int) -> None:
        """Потратить по пять единиц пара на чашку, включая чай в полёте."""
        if isinstance(cups, bool) or not isinstance(cups, int):
            raise TypeError("cups must be an int")
        if cups < 1:
            raise ValueError("cups must be at least 1")
        required = cups * 5.0
        self._check_steam(required)
        self._steam -= required

    def tear_balloon(self) -> None:
        """Порвать оболочку и посадить аппарат без расхода пара."""
        self._balloon_intact = False
        self._is_flying = False

    def patch_balloon(self) -> None:
        """Восстановить оболочку; остальные атрибуты не меняются."""
        self._balloon_intact = True

    def get_status(self) -> dict:
        """Вернуть независимый снимок из шести ключей SPEC 3.4.8."""
        return {
            "name": self.name,
            "steam": self.steam,
            "position_km": self.position_km,
            "is_flying": self.is_flying,
            "balloon_intact": self.balloon_intact,
            "can_fly": self.can_fly,
        }
