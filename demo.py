"""Демонстрация «Пыхтуна» для защиты. Запуск из корня репозитория: python demo.py"""

from samovar_balloon import SamovarBalloon, SamovarBalloonTorn, SamovarCannotSwim

s = SamovarBalloon("Пыхтун", mass_kg=150, balloon_volume_m3=800, max_speed_kmh=40)
print("Грузоподъёмность:", s.lift_capacity_kg, "кг")
print("Полёт 10 км, часов:", s.move(10, "air"))
print("Стена в полёте:", s.can_overcome("wall"))
s.tear_balloon()
print("Ворона клюнула:", s.get_status())
try:
    s.move(5, "air")
except SamovarBalloonTorn as e:
    print("Взлёт:", type(e).__name__, "-", e)
try:
    s.move(1, "water")
except SamovarCannotSwim as e:
    print("Вода:", type(e).__name__, "-", e)
print("Пешком 2 км, часов:", s.move(2, "ground"))
s.patch_balloon()
s.brew_tea(2)
print("Починка и 2 чашки чая:", s.get_status())
