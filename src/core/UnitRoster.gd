class_name UnitRoster
extends RefCounted
## UnitRoster — single source of truth for the v0.1 card hand.
##
## GDD §5 fixes the roster and the costs (Marine 3 / Marauder 4 / Hellion 4 /
## Siege Tank 7). Before this file the costs were hard-coded inside
## UnitSpawner and the icons only existed as files, so the HUD, the card bar
## and the spawner could drift apart. All three now read this table.
##
## The scene paths are preloaded so a typo fails at parse time, not at runtime.

const CARDS: Array[Dictionary] = [
	{
		"id": "marine",
		"name": "Marine",
		"cost": 3,
		"rarity": "Common",
		"scene": preload("res://scenes/units/marine.tscn"),
		"icon": "res://assets/sprites/ui/icon_marine.png",
	},
	{
		"id": "marauder",
		"name": "Marauder",
		"cost": 4,
		"rarity": "Rare",
		"scene": preload("res://scenes/units/marauder.tscn"),
		"icon": "res://assets/sprites/ui/icon_marauder.png",
	},
	{
		"id": "hellion",
		"name": "Hellion",
		"cost": 4,
		"rarity": "Rare",
		"scene": preload("res://scenes/units/hellion.tscn"),
		"icon": "res://assets/sprites/ui/icon_hellion.png",
	},
	{
		"id": "siege_tank",
		"name": "Siege Tank",
		"cost": 7,
		"rarity": "Epic",
		"scene": preload("res://scenes/units/siege_tank.tscn"),
		"icon": "res://assets/sprites/ui/icon_siege_tank.png",
	},
]


## The card record for `id`, or an empty Dictionary when unknown.
static func card(id: String) -> Dictionary:
	for c in CARDS:
		if c["id"] == id:
			return c
	return {}


static func ids() -> Array[String]:
	var out: Array[String] = []
	for c in CARDS:
		out.append(c["id"])
	return out


static func cost(id: String) -> int:
	var c := card(id)
	return int(c["cost"]) if not c.is_empty() else -1
