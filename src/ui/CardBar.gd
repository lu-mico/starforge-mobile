class_name CardBar
extends Control
## CardBar — the bottom hand (GDD §5: 4 cards, tap to select).
##
## 4 cards of 160x128 with a 16px gap = 688px, centred in the 720px viewport.
## The bar sits at the bottom of the screen, above the help line.

signal card_selected(card_id: String)

const CARD_GAP: float = 16.0
const BAR_HEIGHT: float = UnitCard.CARD_SIZE.y

var _cards: Array[UnitCard] = []
var _selected_id: String = ""


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	for child in get_children():
		child.queue_free()
	_cards.clear()

	for c in UnitRoster.CARDS:
		var card := UnitCard.new()
		card.name = "Card_%s" % c["id"]
		card.setup(c["id"], int(c["cost"]), c["name"], c["icon"])
		card.card_pressed.connect(_on_card_pressed)
		add_child(card)
		_cards.append(card)

	_layout()


func _layout() -> void:
	var card_w: float = UnitCard.CARD_SIZE.x
	var total: float = _cards.size() * card_w + max(0, _cards.size() - 1) * CARD_GAP
	# the bar spans the viewport width; fall back to the design width when the
	# control has not been sized yet (headless script runs)
	var usable: float = size.x if size.x > 1.0 else 720.0
	var x: float = (usable - total) * 0.5
	for card in _cards:
		card.position = Vector2(x, 0.0)
		x += card_w + CARD_GAP
	# size is driven by the scene anchors; custom_minimum_size only declares
	# the minimum this bar needs.
	custom_minimum_size = Vector2(720.0, BAR_HEIGHT)


func _on_card_pressed(card: UnitCard) -> void:
	if card.card_id == _selected_id:
		_selected_id = ""
		for c in _cards:
			c.set_selected(false)
		card_selected.emit("")
		return
	_selected_id = card.card_id
	for c in _cards:
		c.set_selected(c.card_id == _selected_id)
	card_selected.emit(_selected_id)


func selected_id() -> String:
	return _selected_id


func clear_selection() -> void:
	_selected_id = ""
	for c in _cards:
		c.set_selected(false)


func card_by_id(id: String) -> UnitCard:
	for c in _cards:
		if c.card_id == id:
			return c
	return null


## Refresh the affordable/unaffordable tint of every card.
func refresh_affordability(current_minerals: int) -> void:
	for c in _cards:
		c.set_affordable(current_minerals >= c.cost)
