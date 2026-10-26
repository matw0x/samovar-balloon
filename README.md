# Самоварный аэростат «Пыхтун»

Учебный класс Python по SPEC.md v0.3: летает за счёт оболочки, ходит на ножках и заваривает чай. Воду не переносит. Запас пара расходуется на движение и чай, восстанавливается углём.

Автор ТЗ и тестов — Матвей Крашенинников. Разработчик — Илья Резниченко.

## Запуск

Нужен Python 3.10 или новее. Внешних зависимостей нет.
Из корня репозитория:

```sh
python -m unittest discover -s tests -v
```

В Windows вместо `python` также можно использовать `py -3`.
Набор содержит 34 авторских теста: 29 модульных и 5 сценарных.

## Пример

```python
from samovar_balloon import SamovarBalloon, SamovarOutOfSteam

samovar = SamovarBalloon("Пыхтун", 150, 800, 40)
print(samovar.move(20, "air"))  # 0.5 часа; пар 60
samovar.move(4, "ground")      # посадка; пар 48
samovar.brew_tea(4)            # пар 28

try:
    samovar.move(15, "air")
except SamovarOutOfSteam as error:
    print(error.required, error.available)  # 30.0, 28.0

samovar.add_coal(50)
samovar.move(15, "air")
print(samovar.get_status())    # пар 48, путь 39, аппарат в воздухе
```

Публичные атрибуты доступны только для чтения. Ошибка метода не меняет состояние. `can_fly` описывает состояние аппарата, а запас пара на конкретную дистанцию проверяет `move`.

Контракт и кейсы — в SPEC.md и TEST_CASES.md. Вопросы разработчика и границы проверки — в BUGREPORT.md. Исходные ТЗ и тесты при реализации не изменялись.
