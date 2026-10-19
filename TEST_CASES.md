# Test Case Specification: Самоварный аэростат «Пыхтун»

Версия: 0.3 (к SPEC.md v0.3)

Эталонный аппарат (если не сказано иное): `SamovarBalloon("Пыхтун", mass_kg=150, balloon_volume_m3=800, max_speed_kmh=40, steam=100)`. Его грузоподъёмность 200 кг.

Соотношение: 29 модульных / 5 сценарных ≈ 85 / 15.

## Модульные тесты (module, AAA)

| ID | Тип | Источник | Предусловие | Вход | Ожидание | Приоритет |
|---|---|---|---|---|---|---|
| TC-01 | module | SPEC 3.2, 3.3 | — | а) mass_kg=150, balloon_volume_m3=800, max_speed_kmh=40 (все int), steam не передан; б) то же, steam=40 (int) | атрибуты равны входу; steam=100.0; position_km=0.0; is_flying=False; balloon_intact=True; lift_capacity_kg=200.0; can_fly=True; все числовые атрибуты типа float (в т. ч. steam=40.0 в б) | high |
| TC-02 | module | SPEC 3.2 | — | name="" ; name="   " | ValueError | high |
| TC-03 | module | SPEC 3.2 | — | mass_kg, balloon_volume_m3, max_speed_kmh = 0 и -1 | ValueError | high |
| TC-04 | module | SPEC 3.2, 5 | — | steam=-0.1 ; steam=100.1 ; steam=0 ; steam=100 | -0.1 и 100.1 → ValueError; 0 и 100 → объект создан | high |
| TC-05 | module | SPEC 3.0, 3.2 | — | name=123 ; name=None ; mass_kg="150" ; mass_kg=True ; balloon_volume_m3=None ; balloon_volume_m3=True ; max_speed_kmh=True ; steam="50" ; steam=True | TypeError | medium |
| TC-06 | module | SPEC 3.3 | эталон | присвоение любого публичного атрибута | AttributeError | medium |
| TC-07 | module | SPEC 3.4.1 | эталон | move(20, "air") | вернул 0.5; steam=60; position_km=20; is_flying=True | high |
| TC-08 | module | SPEC 3.4.1 | после move(1, "air"): steam=98, position=1 | move(4, "ground") | вернул 0.4; steam=86; position_km=5; is_flying=False | high |
| TC-09 | module | SPEC 3.4.1 | эталон | move(1, "water") | SamovarCannotSwim; состояние не изменилось | high |
| TC-10 | module | SPEC 3.4.1 | эталон | move(0, "air") ; move(-5, "air") ; move(1, "space") ; move(1, "") | ValueError; состояние не изменилось | high |
| TC-11 | module | SPEC 3.0, 3.4.1 | эталон | move("10", "air") ; move(True, "air") ; move(None, "air") ; move(1, 1) | TypeError | medium |
| TC-12 | module | SPEC 3.0, 3.4.1 | steam=10 | move(30, "air") | SamovarOutOfSteam, required=60, available=10; steam=10; position_km=0; is_flying=False | high |
| TC-13 | module | SPEC 3.4.1, 5 | steam=100 | move(50, "air") | вернул 1.25; steam=0.0; position_km=50 | high |
| TC-14 | module | SPEC 2, 3.3, 3.4.1, 5 | а) mass_kg=250; б) mass_kg=200 (объём 800) | move(1, "air"), затем move(1, "ground") для а) | а) lift=200, can_fly=False, SamovarTooHeavy, состояние не изменилось, по земле идёт (вернул 0.1); б) can_fly=True, полёт успешен | high |
| TC-15 | module | SPEC 6.3 | несколько нарушений одновременно | см. колонку «Ожидание» | порвана + steam=0 → SamovarBalloonTorn; mass=250 + steam=0 → SamovarTooHeavy; порвана + mass=250 → SamovarBalloonTorn; steam=0, move(1, "water") → SamovarCannotSwim; move(0, "water") → ValueError; move("1", "space") → TypeError | medium |
| TC-16 | module | SPEC 3.4.3 | эталон; отдельно steam=10; отдельно порванная оболочка | calculate_steam(10, "air") ; (10, "ground") ; (1000, "air") при steam=10 ; (10, "air") при порванной | 20 ; 30 ; 2000 без исключения ; 20 без исключения; состояние не изменилось | high |
| TC-17 | module | SPEC 3.4.3 | эталон | calculate_steam(1, "water") ; (0, "air") ; (1, "space") ; ("1", "air") ; (True, "air") ; (1, 1) | SamovarCannotSwim ; ValueError ; ValueError ; TypeError ; TypeError ; TypeError | medium |
| TC-18 | module | SPEC 3.4.2 | 6 состояний: на земле; в воздухе; на земле с порванной оболочкой; перегруз 250 кг; steam=0 на земле; steam=0 в воздухе (steam=2, затем move(1, "air")) | can_overcome("wall" / "river" / "low_bridge") | земля: F / T / T; воздух: T / T / F; порвана: F / F / T; перегруз: F / F / T; steam=0 на земле: F / F / T; steam=0 в воздухе: T / F / F; пар и позиция не изменились | high |
| TC-19 | module | SPEC 3.4.2 | эталон | can_overcome("mountain") ; ("") ; (42) ; (None) | ValueError ; ValueError ; TypeError ; TypeError | medium |
| TC-20 | module | SPEC 3.4.4, 5 | steam=20 ; steam=50 ; steam=100 | add_coal(50) ; add_coal(1000) ; add_coal(0.5) | 70 ; 100 ; 100; steam всегда типа float | high |
| TC-21 | module | SPEC 3.4.4 | steam=50 | add_coal(0) ; (-5) ; ("10") ; (True) | ValueError ; ValueError ; TypeError ; TypeError; steam=50 | medium |
| TC-22 | module | SPEC 3.4.5 | а) после move(10, "air"): steam=80; б) steam=20; в) оболочка порвана, steam=100 | а) brew_tea(4); б) brew_tea(4); в) brew_tea(2) | а) steam=60, position_km=10, is_flying=True; б) steam=0; в) steam=90, balloon_intact=False | high |
| TC-23 | module | SPEC 3.4.5 | эталон | brew_tea(0) ; (-1) ; (2.5) ; (True) ; ("3") | ValueError ; ValueError ; TypeError ; TypeError ; TypeError; steam=100 | medium |
| TC-24 | module | SPEC 3.4.5 | steam=10 | brew_tea(3) | SamovarOutOfSteam, required=15, available=10; steam=10 | high |
| TC-25 | module | SPEC 3.4.6 | а) после move(10, "air"): steam=80; б) на земле, steam=100 | а) tear_balloon() дважды; б) tear_balloon() | а) balloon_intact=False; is_flying=False; can_fly=False; steam=80; position_km=10; второй вызов без ошибок; б) balloon_intact=False; is_flying=False; steam=100; position_km=0 | high |
| TC-26 | module | SPEC 3.4.7 | а) оболочка порвана; б) оболочка цела; в) оболочка порвана, steam=0 | patch_balloon() | а) balloon_intact=True, can_fly=True, is_flying=False; б) без ошибок, balloon_intact=True; в) balloon_intact=True, can_fly=False | high |
| TC-27 | module | SPEC 3.4.8 | после move(10, "air") | get_status(), затем изменить словарь | ключи ровно {name, steam, position_km, is_flying, balloon_intact, can_fly}; значения "Пыхтун", 80, 10, True, True, True; изменение словаря не меняет объект | medium |
| TC-28 | module | SPEC 6.1 | — | issubclass(...) | 4 доменных ⊂ SamovarError ⊂ CrazyVehicleError ⊂ Exception; SamovarOutOfSteam имеет required/available | medium |
| TC-34 | module | SPEC 3.0, 3.2, 3.4.1, 3.4.3, 3.4.4 | эталон | конструктор: mass_kg=nan, balloon_volume_m3=inf, max_speed_kmh=-inf, steam=nan ; move(inf, "air") ; move(nan, "air") ; calculate_steam(inf, "air") ; add_coal(inf) ; add_coal(nan) | ValueError; состояние не изменилось | medium |

## Сценарные тесты (scenario, GWT)

| ID | Тип | Источник | Вход | Ожидание | Приоритет |
|---|---|---|---|---|---|
| TC-29 | scenario | SPEC 4.2, сц. 5 | все шаги «Доставка самовара на дачу» | position_km=39; steam=48; is_flying=True; промежуточный SamovarOutOfSteam(30, 28) | high |
| TC-30 | scenario | SPEC 4.2, сц. 6 | все шаги «Ворона-диверсант» | position_km=24; steam=50; is_flying=True; balloon_intact=True; промежуточный SamovarBalloonTorn | high |
| TC-31 | scenario | SPEC 4.2, сц. 7 | все шаги «Тяжеловес у реки» | position_km=10; steam=100; is_flying=False; can_fly=False | high |
| TC-32 | scenario | SPEC 4.2, сц. 8 | все шаги «Ночной перелёт на последнем угольке» | после 50 км: can_fly=False, can_overcome wall=T, river=F, low_bridge=F; итог: position_km=55; steam=0; is_flying=True | medium |
| TC-33 | scenario | SPEC 4.2, сц. 9 | все шаги «Впритык по грузоподъёмности» | position_km=20; steam=0; is_flying=False; balloon_intact=True; can_fly=False | medium |
