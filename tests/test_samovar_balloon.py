"""Тесты для самоварного аэростата «Пыхтун» (SPEC.md v0.3, TEST_CASES.md v0.3).

Запуск из корня репозитория:

    python -m unittest discover -s tests -v

Модульные тесты построены по паттерну AAA (Arrange-Act-Assert),
сценарные — по Given-When-Then через тестовые обёртки Pilot и Crow.
Каждый тест содержит ID своего тест-кейса в имени и в docstring.
"""

import math
import unittest

from samovar_balloon import (
    CrazyVehicleError,
    SamovarBalloon,
    SamovarBalloonTorn,
    SamovarCannotSwim,
    SamovarError,
    SamovarOutOfSteam,
    SamovarTooHeavy,
)

PLACES = 6


def make_samovar(**overrides):
    """Эталонный аппарат из SPEC 4: 150 кг, 800 м³, 40 км/ч, пар 100."""
    params = {
        "name": "Пыхтун",
        "mass_kg": 150.0,
        "balloon_volume_m3": 800.0,
        "max_speed_kmh": 40.0,
        "steam": 100.0,
    }
    params.update(overrides)
    return SamovarBalloon(**params)


def snapshot(samovar):
    """Наблюдаемое состояние аппарата для проверки атомарности."""
    return (
        samovar.steam,
        samovar.position_km,
        samovar.is_flying,
        samovar.balloon_intact,
    )


# ---------------------------------------------------------------------------
# Тестовые обёртки для сценариев (не являются частью реализации)
# ---------------------------------------------------------------------------


class Pilot:
    """Эмулятор пилота: управляет аппаратом на доменном языке."""

    def __init__(self, samovar):
        self._samovar = samovar

    def лететь(self, distance_km):
        return self._samovar.move(distance_km, "air")

    def идти_пешком(self, distance_km):
        return self._samovar.move(distance_km, "ground")

    def переплыть(self, distance_km):
        return self._samovar.move(distance_km, "water")

    def может_преодолеть(self, obstacle):
        return self._samovar.can_overcome(obstacle)

    def заварить_чай(self, cups):
        self._samovar.brew_tea(cups)

    def подкинуть_угля(self, amount):
        self._samovar.add_coal(amount)

    def залатать_оболочку(self):
        self._samovar.patch_balloon()


class Crow:
    """Ворона-диверсант: событие внешнего мира, рвёт оболочку."""

    def клюнуть(self, samovar):
        samovar.tear_balloon()


# ---------------------------------------------------------------------------
# Модульные тесты (AAA)
# ---------------------------------------------------------------------------


class TestConstructor(unittest.TestCase):
    """SPEC 3.2, 3.3."""

    def test_tc01_init_valid_defaults(self):
        """TC-01. Корректное создание и начальное состояние."""
        # Arrange / Act
        samovar = SamovarBalloon(
            "Пыхтун", mass_kg=150, balloon_volume_m3=800, max_speed_kmh=40
        )

        # Assert
        self.assertEqual(samovar.name, "Пыхтун")
        self.assertAlmostEqual(samovar.mass_kg, 150.0, places=PLACES)
        self.assertAlmostEqual(samovar.balloon_volume_m3, 800.0, places=PLACES)
        self.assertAlmostEqual(samovar.max_speed_kmh, 40.0, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 100.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 0.0, places=PLACES)
        self.assertIs(samovar.is_flying, False)
        self.assertIs(samovar.balloon_intact, True)
        self.assertAlmostEqual(samovar.lift_capacity_kg, 200.0, places=PLACES)
        self.assertIs(samovar.can_fly, True)
        for attr in ("mass_kg", "balloon_volume_m3", "max_speed_kmh",
                     "steam", "position_km", "lift_capacity_kg"):
            with self.subTest(attr=attr):
                self.assertIsInstance(getattr(samovar, attr), float)

        with_int_steam = SamovarBalloon(
            "Пыхтун", mass_kg=150, balloon_volume_m3=800, max_speed_kmh=40,
            steam=40,
        )
        self.assertIsInstance(with_int_steam.steam, float)
        self.assertAlmostEqual(with_int_steam.steam, 40.0, places=PLACES)

    def test_tc02_init_empty_name_raises(self):
        """TC-02. Пустое имя или имя из пробелов → ValueError."""
        for bad_name in ("", "   "):
            with self.subTest(name=bad_name):
                # Act / Assert
                with self.assertRaises(ValueError):
                    make_samovar(name=bad_name)

    def test_tc03_init_non_positive_dimensions_raise(self):
        """TC-03. Масса, объём, скорость ≤ 0 → ValueError."""
        for param in ("mass_kg", "balloon_volume_m3", "max_speed_kmh"):
            for value in (0, -1):
                with self.subTest(param=param, value=value):
                    with self.assertRaises(ValueError):
                        make_samovar(**{param: value})

    def test_tc04_init_steam_range(self):
        """TC-04. Пар вне 0…100 → ValueError; границы 0 и 100 допустимы."""
        for bad_steam in (-0.1, 100.1):
            with self.subTest(steam=bad_steam):
                with self.assertRaises(ValueError):
                    make_samovar(steam=bad_steam)

        for ok_steam in (0, 100):
            with self.subTest(steam=ok_steam):
                samovar = make_samovar(steam=ok_steam)
                self.assertAlmostEqual(samovar.steam, float(ok_steam),
                                       places=PLACES)

    def test_tc05_init_wrong_types_raise(self):
        """TC-05. Неверные типы параметров конструктора → TypeError."""
        cases = [
            {"name": 123},
            {"name": None},
            {"mass_kg": "150"},
            {"mass_kg": True},
            {"balloon_volume_m3": None},
            {"balloon_volume_m3": True},
            {"max_speed_kmh": True},
            {"steam": "50"},
            {"steam": True},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(TypeError):
                    make_samovar(**overrides)

    def test_tc06_attributes_read_only(self):
        """TC-06. Публичные атрибуты доступны только для чтения."""
        # Arrange
        samovar = make_samovar()
        assignments = [
            ("name", "Другой"),
            ("mass_kg", 1.0),
            ("balloon_volume_m3", 1.0),
            ("max_speed_kmh", 1.0),
            ("steam", 50.0),
            ("position_km", 5.0),
            ("is_flying", True),
            ("balloon_intact", False),
            ("lift_capacity_kg", 1.0),
            ("can_fly", False),
        ]
        for attr, value in assignments:
            with self.subTest(attr=attr):
                # Act / Assert
                with self.assertRaises(AttributeError):
                    setattr(samovar, attr, value)


class TestMove(unittest.TestCase):
    """SPEC 3.4.1, 6.3."""

    def test_tc07_move_air(self):
        """TC-07. Полёт: скорость max_speed, расход 2 ед./км."""
        # Arrange
        samovar = make_samovar()

        # Act
        hours = samovar.move(20, "air")

        # Assert
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 60.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 20.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

    def test_tc08_move_ground_after_flight(self):
        """TC-08. Ходьба: скорость ×0.25, расход 3 ед./км, посадка."""
        # Arrange
        samovar = make_samovar()
        samovar.move(1, "air")

        # Act
        hours = samovar.move(4, "ground")

        # Assert
        self.assertAlmostEqual(hours, 0.4, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 86.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 5.0, places=PLACES)
        self.assertIs(samovar.is_flying, False)

    def test_tc09_move_water_raises_cannot_swim(self):
        """TC-09. Вода → SamovarCannotSwim, состояние не меняется."""
        # Arrange
        samovar = make_samovar()
        before = snapshot(samovar)

        # Act / Assert
        with self.assertRaises(SamovarCannotSwim):
            samovar.move(1, "water")
        self.assertEqual(snapshot(samovar), before)

    def test_tc10_move_invalid_values_raise(self):
        """TC-10. Дистанция ≤ 0 или неизвестная среда → ValueError."""
        # Arrange
        samovar = make_samovar()
        before = snapshot(samovar)

        for args in ((0, "air"), (-5, "air"), (1, "space"), (1, "")):
            with self.subTest(args=args):
                # Act / Assert
                with self.assertRaises(ValueError):
                    samovar.move(*args)
        self.assertEqual(snapshot(samovar), before)

    def test_tc11_move_wrong_types_raise(self):
        """TC-11. Неверные типы аргументов move → TypeError."""
        # Arrange
        samovar = make_samovar()

        for args in (("10", "air"), (True, "air"), (None, "air"), (1, 1)):
            with self.subTest(args=args):
                # Act / Assert
                with self.assertRaises(TypeError):
                    samovar.move(*args)

    def test_tc12_move_out_of_steam(self):
        """TC-12. Нехватка пара → SamovarOutOfSteam, состояние не меняется."""
        # Arrange
        samovar = make_samovar(steam=10)
        before = snapshot(samovar)

        # Act
        with self.assertRaises(SamovarOutOfSteam) as ctx:
            samovar.move(30, "air")

        # Assert
        self.assertAlmostEqual(ctx.exception.required, 60.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 10.0, places=PLACES)
        self.assertEqual(snapshot(samovar), before)

    def test_tc13_move_spends_all_steam_exactly(self):
        """TC-13. Расход ровно равен запасу — перемещение разрешено."""
        # Arrange
        samovar = make_samovar(steam=100)

        # Act
        hours = samovar.move(50, "air")

        # Assert
        self.assertAlmostEqual(hours, 1.25, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 50.0, places=PLACES)

    def test_tc14_lift_capacity_boundary(self):
        """TC-14. Грузоподъёмность: перегруз запрещает полёт, равенство — нет."""
        with self.subTest(case="перегруз 250 кг"):
            # Arrange
            heavy = make_samovar(mass_kg=250)
            before = snapshot(heavy)

            # Act / Assert
            self.assertAlmostEqual(heavy.lift_capacity_kg, 200.0,
                                   places=PLACES)
            self.assertIs(heavy.can_fly, False)
            with self.assertRaises(SamovarTooHeavy):
                heavy.move(1, "air")
            self.assertEqual(snapshot(heavy), before)
            self.assertAlmostEqual(heavy.move(1, "ground"), 0.1,
                                   places=PLACES)

        with self.subTest(case="ровно 200 кг"):
            # Arrange
            exact = make_samovar(mass_kg=200)

            # Act
            exact.move(1, "air")

            # Assert
            self.assertIs(exact.is_flying, True)

    def test_tc15_move_check_priority(self):
        """TC-15. При нескольких нарушениях — первое по порядку SPEC 6.3."""
        with self.subTest(case="порвана + нет пара"):
            samovar = make_samovar(steam=0)
            samovar.tear_balloon()
            with self.assertRaises(SamovarBalloonTorn):
                samovar.move(1, "air")

        with self.subTest(case="перегруз + нет пара"):
            samovar = make_samovar(mass_kg=250, steam=0)
            with self.assertRaises(SamovarTooHeavy):
                samovar.move(1, "air")

        with self.subTest(case="порвана + перегруз"):
            samovar = make_samovar(mass_kg=250)
            samovar.tear_balloon()
            with self.assertRaises(SamovarBalloonTorn):
                samovar.move(1, "air")

        with self.subTest(case="вода + нет пара"):
            samovar = make_samovar(steam=0)
            with self.assertRaises(SamovarCannotSwim):
                samovar.move(1, "water")

        with self.subTest(case="вода + нулевая дистанция"):
            samovar = make_samovar()
            with self.assertRaises(ValueError):
                samovar.move(0, "water")

        with self.subTest(case="неверный тип + неизвестная среда"):
            samovar = make_samovar()
            with self.assertRaises(TypeError):
                samovar.move("1", "space")


class TestCalculateSteam(unittest.TestCase):
    """SPEC 3.4.3."""

    def test_tc16_calculate_steam_values(self):
        """TC-16. Расчёт расхода без изменения состояния и без проверок домена."""
        # Arrange
        samovar = make_samovar()
        before = snapshot(samovar)

        # Act / Assert
        self.assertAlmostEqual(samovar.calculate_steam(10, "air"), 20.0,
                               places=PLACES)
        self.assertAlmostEqual(samovar.calculate_steam(10, "ground"), 30.0,
                               places=PLACES)
        self.assertEqual(snapshot(samovar), before)

        poor = make_samovar(steam=10)
        self.assertAlmostEqual(poor.calculate_steam(1000, "air"), 2000.0,
                               places=PLACES)
        self.assertAlmostEqual(poor.steam, 10.0, places=PLACES)

        torn = make_samovar()
        torn.tear_balloon()
        self.assertAlmostEqual(torn.calculate_steam(10, "air"), 20.0,
                               places=PLACES)

    def test_tc17_calculate_steam_errors(self):
        """TC-17. Ошибки параметров и вода в calculate_steam."""
        # Arrange
        samovar = make_samovar()

        # Act / Assert
        with self.assertRaises(SamovarCannotSwim):
            samovar.calculate_steam(1, "water")
        for args in ((0, "air"), (1, "space")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    samovar.calculate_steam(*args)
        for args in (("1", "air"), (True, "air"), (1, 1)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    samovar.calculate_steam(*args)


class TestCanOvercome(unittest.TestCase):
    """SPEC 3.4.2."""

    def _states(self):
        on_ground = make_samovar()

        flying = make_samovar()
        flying.move(1, "air")

        torn = make_samovar()
        torn.tear_balloon()

        heavy = make_samovar(mass_kg=250)

        empty_on_ground = make_samovar(steam=0)

        empty_in_air = make_samovar(steam=2)
        empty_in_air.move(1, "air")

        return {
            "на земле": (on_ground,
                         {"wall": False, "river": True, "low_bridge": True}),
            "в воздухе": (flying,
                          {"wall": True, "river": True, "low_bridge": False}),
            "порвана": (torn,
                        {"wall": False, "river": False, "low_bridge": True}),
            "перегруз": (heavy,
                         {"wall": False, "river": False, "low_bridge": True}),
            "пар 0 на земле": (empty_on_ground,
                               {"wall": False, "river": False,
                                "low_bridge": True}),
            "пар 0 в воздухе": (empty_in_air,
                                {"wall": True, "river": False,
                                 "low_bridge": False}),
        }

    def test_tc18_can_overcome_matrix(self):
        """TC-18. Правила препятствий в разных состояниях; состояние не меняется."""
        for state_name, (samovar, expected) in self._states().items():
            for obstacle, result in expected.items():
                with self.subTest(state=state_name, obstacle=obstacle):
                    # Arrange
                    before = snapshot(samovar)

                    # Act
                    actual = samovar.can_overcome(obstacle)

                    # Assert
                    self.assertIs(actual, result)
                    self.assertEqual(snapshot(samovar), before)

    def test_tc19_can_overcome_invalid(self):
        """TC-19. Неизвестное препятствие → ValueError, не строка → TypeError."""
        # Arrange
        samovar = make_samovar()

        # Act / Assert
        for obstacle in ("mountain", ""):
            with self.subTest(obstacle=obstacle):
                with self.assertRaises(ValueError):
                    samovar.can_overcome(obstacle)
        for obstacle in (42, None):
            with self.subTest(obstacle=obstacle):
                with self.assertRaises(TypeError):
                    samovar.can_overcome(obstacle)


class TestAddCoal(unittest.TestCase):
    """SPEC 3.4.4."""

    def test_tc20_add_coal(self):
        """TC-20. Уголь пополняет пар, но не выше 100."""
        for start, amount, expected in ((20, 50, 70.0),
                                        (50, 1000, 100.0),
                                        (100, 0.5, 100.0)):
            with self.subTest(start=start, amount=amount):
                # Arrange
                samovar = make_samovar(steam=start)

                # Act
                result = samovar.add_coal(amount)

                # Assert
                self.assertIsNone(result)
                self.assertAlmostEqual(samovar.steam, expected, places=PLACES)
                self.assertIsInstance(samovar.steam, float)

    def test_tc21_add_coal_invalid(self):
        """TC-21. Неположительный или нечисловой уголь отвергается."""
        # Arrange
        samovar = make_samovar(steam=50)

        # Act / Assert
        for amount in (0, -5):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    samovar.add_coal(amount)
        for amount in ("10", True):
            with self.subTest(amount=amount):
                with self.assertRaises(TypeError):
                    samovar.add_coal(amount)
        self.assertAlmostEqual(samovar.steam, 50.0, places=PLACES)


class TestBrewTea(unittest.TestCase):
    """SPEC 3.4.5."""

    def test_tc22_brew_tea(self):
        """TC-22. Чай: 5 ед. пара за чашку, позиция и полёт не меняются."""
        with self.subTest(case="в полёте"):
            # Arrange
            samovar = make_samovar()
            samovar.move(10, "air")

            # Act
            samovar.brew_tea(4)

            # Assert
            self.assertAlmostEqual(samovar.steam, 60.0, places=PLACES)
            self.assertAlmostEqual(samovar.position_km, 10.0, places=PLACES)
            self.assertIs(samovar.is_flying, True)

        with self.subTest(case="весь пар до нуля"):
            samovar = make_samovar(steam=20)
            samovar.brew_tea(4)
            self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)

        with self.subTest(case="с порванной оболочкой"):
            samovar = make_samovar()
            samovar.tear_balloon()
            samovar.brew_tea(2)
            self.assertAlmostEqual(samovar.steam, 90.0, places=PLACES)
            self.assertIs(samovar.balloon_intact, False)

    def test_tc23_brew_tea_invalid(self):
        """TC-23. Чашек < 1 → ValueError; не int → TypeError."""
        # Arrange
        samovar = make_samovar()

        # Act / Assert
        for cups in (0, -1):
            with self.subTest(cups=cups):
                with self.assertRaises(ValueError):
                    samovar.brew_tea(cups)
        for cups in (2.5, True, "3"):
            with self.subTest(cups=cups):
                with self.assertRaises(TypeError):
                    samovar.brew_tea(cups)
        self.assertAlmostEqual(samovar.steam, 100.0, places=PLACES)

    def test_tc24_brew_tea_out_of_steam(self):
        """TC-24. Не хватает пара на чай → SamovarOutOfSteam."""
        # Arrange
        samovar = make_samovar(steam=10)

        # Act
        with self.assertRaises(SamovarOutOfSteam) as ctx:
            samovar.brew_tea(3)

        # Assert
        self.assertAlmostEqual(ctx.exception.required, 15.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 10.0, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 10.0, places=PLACES)


class TestBalloon(unittest.TestCase):
    """SPEC 3.4.6, 3.4.7."""

    def test_tc25_tear_balloon(self):
        """TC-25. Разрыв оболочки: в полёте — аварийная посадка; на земле."""
        with self.subTest(case="в полёте"):
            # Arrange
            samovar = make_samovar()
            samovar.move(10, "air")

            # Act
            samovar.tear_balloon()
            samovar.tear_balloon()

            # Assert
            self.assertIs(samovar.balloon_intact, False)
            self.assertIs(samovar.is_flying, False)
            self.assertIs(samovar.can_fly, False)
            self.assertAlmostEqual(samovar.steam, 80.0, places=PLACES)
            self.assertAlmostEqual(samovar.position_km, 10.0, places=PLACES)

        with self.subTest(case="на земле"):
            samovar = make_samovar()
            samovar.tear_balloon()
            self.assertIs(samovar.balloon_intact, False)
            self.assertIs(samovar.is_flying, False)
            self.assertAlmostEqual(samovar.steam, 100.0, places=PLACES)
            self.assertAlmostEqual(samovar.position_km, 0.0, places=PLACES)

    def test_tc26_patch_balloon(self):
        """TC-26. Починка возвращает возможность полёта; повтор безопасен."""
        with self.subTest(case="после разрыва"):
            # Arrange
            samovar = make_samovar()
            samovar.tear_balloon()

            # Act
            samovar.patch_balloon()

            # Assert
            self.assertIs(samovar.balloon_intact, True)
            self.assertIs(samovar.can_fly, True)
            self.assertIs(samovar.is_flying, False)

        with self.subTest(case="оболочка и так цела"):
            samovar = make_samovar()
            samovar.patch_balloon()
            self.assertIs(samovar.balloon_intact, True)

        with self.subTest(case="пара нет"):
            samovar = make_samovar(steam=0)
            samovar.tear_balloon()
            samovar.patch_balloon()
            self.assertIs(samovar.balloon_intact, True)
            self.assertIs(samovar.can_fly, False)


class TestStatusAndExceptions(unittest.TestCase):
    """SPEC 3.4.8, 6.1."""

    def test_tc27_get_status(self):
        """TC-27. Статус: ровно нужные ключи, верные значения, это копия."""
        # Arrange
        samovar = make_samovar()
        samovar.move(10, "air")

        # Act
        status = samovar.get_status()

        # Assert
        self.assertEqual(
            set(status),
            {"name", "steam", "position_km", "is_flying",
             "balloon_intact", "can_fly"},
        )
        self.assertEqual(status["name"], "Пыхтун")
        self.assertAlmostEqual(status["steam"], 80.0, places=PLACES)
        self.assertAlmostEqual(status["position_km"], 10.0, places=PLACES)
        self.assertIs(status["is_flying"], True)
        self.assertIs(status["balloon_intact"], True)
        self.assertIs(status["can_fly"], True)

        status["steam"] = 0.0
        status["is_flying"] = False
        self.assertAlmostEqual(samovar.steam, 80.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

    def test_tc28_exception_hierarchy(self):
        """TC-28. Иерархия доменных исключений."""
        for exc in (SamovarCannotSwim, SamovarOutOfSteam,
                    SamovarTooHeavy, SamovarBalloonTorn):
            with self.subTest(exc=exc.__name__):
                self.assertTrue(issubclass(exc, SamovarError))
        self.assertTrue(issubclass(SamovarError, CrazyVehicleError))
        self.assertTrue(issubclass(CrazyVehicleError, Exception))

        error = SamovarOutOfSteam(required=6, available=2)
        self.assertAlmostEqual(error.required, 6.0, places=PLACES)
        self.assertAlmostEqual(error.available, 2.0, places=PLACES)

    def test_tc34_non_finite_numbers_raise(self):
        """TC-34. nan, inf и -inf → ValueError, состояние не меняется."""
        nan, inf = math.nan, math.inf
        for overrides in ({"mass_kg": nan}, {"balloon_volume_m3": inf},
                          {"max_speed_kmh": -inf}, {"steam": nan}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    make_samovar(**overrides)

        # Arrange
        samovar = make_samovar(steam=50)
        before = snapshot(samovar)
        calls = [
            ("move(inf)", lambda: samovar.move(inf, "air")),
            ("move(nan)", lambda: samovar.move(nan, "air")),
            ("calculate_steam(inf)", lambda: samovar.calculate_steam(inf, "air")),
            ("add_coal(inf)", lambda: samovar.add_coal(inf)),
            ("add_coal(nan)", lambda: samovar.add_coal(nan)),
        ]
        for label, call in calls:
            with self.subTest(call=label):
                # Act / Assert
                with self.assertRaises(ValueError):
                    call()
                self.assertEqual(snapshot(samovar), before)


# ---------------------------------------------------------------------------
# Сценарные тесты (Given-When-Then)
# ---------------------------------------------------------------------------


class TestScenarios(unittest.TestCase):
    """SPEC 4.2."""

    def test_tc29_dacha_delivery(self):
        """TC-29. Сценарий 5 «Доставка самовара на дачу»."""
        # Given эталонный «Пыхтун» с паром 100 стоит на земле
        samovar = make_samovar()
        pilot = Pilot(samovar)

        # When пилот летит 20 км
        hours = pilot.лететь(20)
        # Then время 0.5 ч, пар 60, пройдено 20 км, в воздухе
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 60.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 20.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

        # When пилот проверяет стену / Then может
        self.assertIs(pilot.может_преодолеть("wall"), True)

        # When пилот садится и идёт пешком 4 км
        hours = pilot.идти_пешком(4)
        # Then время 0.4 ч, пар 48, пройдено 24 км, на земле
        self.assertAlmostEqual(hours, 0.4, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 48.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 24.0, places=PLACES)
        self.assertIs(samovar.is_flying, False)

        # When пилот проверяет низкий мост / Then пройдёт
        self.assertIs(pilot.может_преодолеть("low_bridge"), True)

        # When пилот заваривает 4 чашки / Then пар 28
        pilot.заварить_чай(4)
        self.assertAlmostEqual(samovar.steam, 28.0, places=PLACES)

        # When пилот пытается лететь 15 км
        with self.assertRaises(SamovarOutOfSteam) as ctx:
            pilot.лететь(15)
        # Then нужно 30, есть 28, состояние прежнее
        self.assertAlmostEqual(ctx.exception.required, 30.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 28.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 24.0, places=PLACES)
        self.assertIs(samovar.is_flying, False)

        # When пилот подкидывает 50 угля и летит 15 км
        pilot.подкинуть_угля(50)
        pilot.лететь(15)
        # Then пар 48, пройдено 39 км, в воздухе
        self.assertAlmostEqual(samovar.steam, 48.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 39.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

    def test_tc30_crow_saboteur(self):
        """TC-30. Сценарий 6 «Ворона-диверсант»."""
        # Given эталонный «Пыхтун» с паром 100
        samovar = make_samovar()
        pilot = Pilot(samovar)
        crow = Crow()

        # When пилот летит 10 км
        pilot.лететь(10)
        # Then пар 80, пройдено 10 км, в воздухе
        self.assertAlmostEqual(samovar.steam, 80.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

        # When ворона клюёт оболочку
        crow.клюнуть(samovar)
        # Then аварийная посадка
        self.assertIs(samovar.balloon_intact, False)
        self.assertIs(samovar.is_flying, False)
        self.assertIs(samovar.can_fly, False)

        # When пилот пытается лететь 5 км / Then SamovarBalloonTorn
        with self.assertRaises(SamovarBalloonTorn):
            pilot.лететь(5)
        self.assertAlmostEqual(samovar.steam, 80.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 10.0, places=PLACES)

        # When пилот проверяет реку / Then не может
        self.assertIs(pilot.может_преодолеть("river"), False)

        # When пилот идёт пешком 2 км
        hours = pilot.идти_пешком(2)
        # Then время 0.2 ч, пар 74, пройдено 12 км
        self.assertAlmostEqual(hours, 0.2, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 74.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 12.0, places=PLACES)

        # When пилот латает оболочку
        pilot.залатать_оболочку()
        # Then можно летать, через реку можно
        self.assertIs(samovar.balloon_intact, True)
        self.assertIs(samovar.can_fly, True)
        self.assertIs(samovar.is_flying, False)
        self.assertIs(pilot.может_преодолеть("river"), True)

        # When пилот летит 12 км
        hours = pilot.лететь(12)
        # Then время 0.3 ч, пар 50, пройдено 24 км, в воздухе
        self.assertAlmostEqual(hours, 0.3, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 50.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 24.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

    def test_tc31_heavyweight_at_river(self):
        """TC-31. Сценарий 7 «Тяжеловес у реки»."""
        # Given «Тяжеловес»: 250 кг, 800 м³, 40 км/ч, пар 100
        samovar = make_samovar(name="Тяжеловес", mass_kg=250)
        pilot = Pilot(samovar)
        # Then грузоподъёмность 200, лететь не может
        self.assertAlmostEqual(samovar.lift_capacity_kg, 200.0, places=PLACES)
        self.assertIs(samovar.can_fly, False)

        # When пилот пытается взлететь на 5 км / Then SamovarTooHeavy
        with self.assertRaises(SamovarTooHeavy):
            pilot.лететь(5)
        self.assertAlmostEqual(samovar.position_km, 0.0, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 100.0, places=PLACES)

        # When пилот проверяет реку / Then не может
        self.assertIs(pilot.может_преодолеть("river"), False)

        # When пилот пытается переплыть / Then SamovarCannotSwim
        before = snapshot(samovar)
        with self.assertRaises(SamovarCannotSwim):
            pilot.переплыть(1)
        self.assertEqual(snapshot(samovar), before)

        # When пилот идёт пешком вдоль реки 10 км
        hours = pilot.идти_пешком(10)
        # Then время 1.0 ч, пар 70, пройдено 10 км
        self.assertAlmostEqual(hours, 1.0, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 70.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 10.0, places=PLACES)

        # When на привале 14 чашек чая / Then пар 0
        pilot.заварить_чай(14)
        self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)

        # When пилот пытается пройти ещё 1 км / Then нужно 3, есть 0
        with self.assertRaises(SamovarOutOfSteam) as ctx:
            pilot.идти_пешком(1)
        self.assertAlmostEqual(ctx.exception.required, 3.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)

        # When пилот подкидывает 1000 угля / Then пар 100
        pilot.подкинуть_угля(1000)
        self.assertAlmostEqual(samovar.steam, 100.0, places=PLACES)

        # Then итог
        self.assertAlmostEqual(samovar.position_km, 10.0, places=PLACES)
        self.assertIs(samovar.is_flying, False)
        self.assertIs(samovar.can_fly, False)

    def test_tc32_night_flight_last_coal(self):
        """TC-32. Сценарий 8 «Ночной перелёт на последнем угольке»."""
        # Given эталонный «Пыхтун» с паром 100
        samovar = make_samovar()
        pilot = Pilot(samovar)

        # When пилот летит 50 км
        hours = pilot.лететь(50)
        # Then время 1.25 ч, пар 0, пройдено 50 км, в воздухе
        self.assertAlmostEqual(hours, 1.25, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 50.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)
        # And лететь дальше не может, но стену перелетит, реку — нет
        self.assertIs(samovar.can_fly, False)
        self.assertIs(pilot.может_преодолеть("wall"), True)
        self.assertIs(pilot.может_преодолеть("river"), False)
        self.assertIs(pilot.может_преодолеть("low_bridge"), False)

        # When пилот пытается пролететь 0.5 км / Then нужно 1, есть 0
        with self.assertRaises(SamovarOutOfSteam) as ctx:
            pilot.лететь(0.5)
        self.assertAlmostEqual(ctx.exception.required, 1.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 50.0, places=PLACES)

        # When пилот подкидывает 10 угля / Then пар 10, может лететь
        pilot.подкинуть_угля(10)
        self.assertAlmostEqual(samovar.steam, 10.0, places=PLACES)
        self.assertIs(samovar.can_fly, True)

        # When пилот летит 5 км
        hours = pilot.лететь(5)
        # Then время 0.125 ч, пар 0, пройдено 55 км, в воздухе
        self.assertAlmostEqual(hours, 0.125, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 55.0, places=PLACES)
        self.assertIs(samovar.is_flying, True)

    def test_tc33_exact_lift_capacity(self):
        """TC-33. Сценарий 9 «Впритык по грузоподъёмности»."""
        # Given «Ровня»: 200 кг, 800 м³, 20 км/ч, пар 40
        samovar = make_samovar(name="Ровня", mass_kg=200,
                               max_speed_kmh=20, steam=40)
        pilot = Pilot(samovar)
        crow = Crow()
        # Then масса равна грузоподъёмности, может лететь
        self.assertIs(samovar.can_fly, True)

        # When пилот летит 10 км
        hours = pilot.лететь(10)
        # Then время 0.5 ч, пар 20, пройдено 10 км
        self.assertAlmostEqual(hours, 0.5, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 20.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 10.0, places=PLACES)

        # When ворона клюёт оболочку / Then на земле, оболочка порвана
        crow.клюнуть(samovar)
        self.assertIs(samovar.is_flying, False)
        self.assertIs(samovar.balloon_intact, False)

        # When пилот заваривает 4 чашки / Then пар 0
        pilot.заварить_чай(4)
        self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)

        # When пилот подкидывает 30 угля и идёт пешком 10 км
        pilot.подкинуть_угля(30)
        hours = pilot.идти_пешком(10)
        # Then время 2.0 ч, пар 0, пройдено 20 км
        self.assertAlmostEqual(hours, 2.0, places=PLACES)
        self.assertAlmostEqual(samovar.steam, 0.0, places=PLACES)
        self.assertAlmostEqual(samovar.position_km, 20.0, places=PLACES)

        # When пилот латает оболочку
        pilot.залатать_оболочку()
        # Then оболочка цела, но лететь нельзя — пара 0
        self.assertIs(samovar.balloon_intact, True)
        self.assertIs(samovar.can_fly, False)

        # When пилот пытается лететь 1 км / Then нужно 2, есть 0
        with self.assertRaises(SamovarOutOfSteam) as ctx:
            pilot.лететь(1)
        self.assertAlmostEqual(ctx.exception.required, 2.0, places=PLACES)
        self.assertAlmostEqual(ctx.exception.available, 0.0, places=PLACES)
        self.assertIs(samovar.is_flying, False)


if __name__ == "__main__":
    unittest.main()
