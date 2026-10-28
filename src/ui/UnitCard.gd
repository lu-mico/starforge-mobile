class_name UnitCard
extends Control
## UnitCard — one card in the bottom hand (GDD §5).
##
## Geometry (ASSET_UI_SPEC §3, measured on the delivered PNGs):
##
##   * card_frame.png is 48x64 with patch_margin 10 on all sides, so the
##     nine-slice centre region is 28x44 and the corners carry the rivets.
##     The frame is drawn WIDER than the source (80 wide) so that the widest
##     icon body (siege tank, 52px) fits the 60px interior with slack:
##       interior = 80 - 2*10 = 60 wide, 64 - 2*10 = 44 tall
##   * every icon body measures exactly 40px tall (rows 12..51) and is
##     horizontally centred inside its 64x64 canvas, so all four cards read
##     at the same height and the body sits centred in the frame interior.
##   * the art layer is drawn at 2x (80x64 -> 160x128 on the 720x1280
##     viewport) with nearest filtering; badges are 12x12 -> 24x24.
##
##   Digits are engine-side: the badges are blank plates (ASSET_UI_SPEC §3.4
##   says the number must be rendered on top), so the cost and the available
##   count are Labels drawn over the cost / count plates.

signal card_pressed(card: UnitCard)

const CARD_SRC: Vector2 = Vector2(80.0, 64.0)   # 1x source-space card box
const ART_SCALE: float = 2.0                      # on-screen scale of the art
const CARD_SIZE: Vector2 = CARD_SRC * ART_SCALE  # 160x128 on screen
const FRAME_MARGIN: int = 10                    # patch_margin on all sides
const ICON_SIZE: int = 64                        # icon canvas is 64x64
const BADGE_SIZE: int = 12
const COST_BADGE_POS: Vector2 = Vector2(66.0, 2.0)    # source space, top-right
const COUNT_BADGE_POS: Vector2 = Vector2(66.0, 50.0)  # source space, bottom-right
const SELECT_BADGE_POS: Vector2 = Vector2(2.0, 2.0)   # source space, top-left

var card_id: String = ""
var cost: int = 0
var title: String = ""
var copies: int = 1

var _icon_path: String = ""
var _art: Control
var _frame: NinePatchRect
var _icon: TextureRect
var _cost_badge: TextureRect
var _count_badge: TextureRect
var _select_badge: TextureRect
var _cost_label: Label
var _count_label: Label
var _selected: bool = false


func _ready() -> void:
	custom_minimum_size = CARD_SIZE
	size = CARD_SIZE
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build()
	gui_input.connect(_on_gui_input)


## Configure the card. Safe to call before or after _ready().
func setup(id: String, card_cost: int, card_title: String, icon_path: String) -> void:
	card_id = id
	cost = card_cost
	title = card_title
	_icon_path = icon_path
	tooltip_text = title
	if _icon != null:
		_icon.texture = load(icon_path)
		_icon.position = _icon_position()
	_refresh_labels()


func _build() -> void:
	_art = Control.new()
	_art.name = "Art"
	_art.size = CARD_SRC
	_art.scale = Vector2(ART_SCALE, ART_SCALE)
	_art.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_art.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_art)

	_frame = NinePatchRect.new()
	_frame.name = "Frame"
	_frame.texture = load("res://assets/sprites/ui/card_frame.png")
	_frame.patch_margin_left = FRAME_MARGIN
	_frame.patch_margin_top = FRAME_MARGIN
	_frame.patch_margin_right = FRAME_MARGIN
	_frame.patch_margin_bottom = FRAME_MARGIN
	_frame.axis_stretch_horizontal = NinePatchRect.AXIS_STRETCH_MODE_STRETCH
	_frame.axis_stretch_vertical = NinePatchRect.AXIS_STRETCH_MODE_STRETCH
	_frame.draw_center = true
	_frame.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_frame.size = CARD_SRC
	_art.add_child(_frame)

	_icon = TextureRect.new()
	_icon.name = "Icon"
	_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_icon.stretch_mode = TextureRect.STRETCH_SCALE
	_icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_icon.size = Vector2(ICON_SIZE, ICON_SIZE)
	_icon.texture = load(_icon_path) if _icon_path != "" else null
	_icon.position = _icon_position()
	_art.add_child(_icon)

	_cost_badge = _badge("CostBadge", "res://assets/sprites/ui/card_badge_cost.png", COST_BADGE_POS)
	_count_badge = _badge("CountBadge", "res://assets/sprites/ui/card_badge_count.png", COUNT_BADGE_POS)
	_select_badge = _badge("SelectBadge", "res://assets/sprites/ui/card_badge_frame.png", SELECT_BADGE_POS)
	_select_badge.visible = false

	# Digits live OUTSIDE the scaled art layer so they render at native size.
	_cost_label = _digit("CostLabel", COST_BADGE_POS, Color(0.04, 0.04, 0.08), 12, 0)
	_count_label = _digit("CountLabel", COUNT_BADGE_POS, Color(0.93, 0.96, 1.0), 11, 3)

	_refresh_labels()


## Place the 64x64 icon canvas so the opaque BODY (not the canvas) is centred
## in the frame interior. The body box is measured from the texture itself, so
## the card stays correct if the art is regenerated.
func _icon_position() -> Vector2:
	var interior := Rect2i(
		FRAME_MARGIN, FRAME_MARGIN,
		int(CARD_SRC.x) - FRAME_MARGIN * 2, int(CARD_SRC.y) - FRAME_MARGIN * 2)
	var body := Rect2i(0, 0, ICON_SIZE, ICON_SIZE)
	var tex := _icon.texture as Texture2D
	if tex != null:
		var img := tex.get_image()
		if img != null:
			var used := img.get_used_rect()
			if used.size != Vector2i.ZERO:
				body = used
	# integer maths only: a half-pixel offset would blur the 2x nearest scale
	return Vector2(interior.get_center() - body.get_center())


func _badge(node_name: String, tex_path: String, src_pos: Vector2) -> TextureRect:
	var tr := TextureRect.new()
	tr.name = node_name
	tr.texture = load(tex_path)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tr.size = Vector2(BADGE_SIZE, BADGE_SIZE)
	tr.position = src_pos
	_art.add_child(tr)
	return tr


func _digit(node_name: String, src_pos: Vector2, colour: Color, font_size: int, outline: int) -> Label:
	var lbl := Label.new()
	lbl.name = node_name
	lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.add_theme_font_size_override("font_size", font_size)
	lbl.add_theme_color_override("font_color", colour)
	if outline > 0:
		lbl.add_theme_constant_override("outline_size", outline)
		lbl.add_theme_color_override("font_outline_color", Color(0.04, 0.04, 0.08, 0.9))
	# badge position is source space -> multiply by the art scale for screen space
	lbl.position = src_pos * ART_SCALE
	lbl.size = Vector2(BADGE_SIZE, BADGE_SIZE) * ART_SCALE
	add_child(lbl)
	return lbl


func _refresh_labels() -> void:
	if _cost_label != null:
		_cost_label.text = str(cost)
	if _count_label != null:
		# the count plate only earns its space when there is more than one copy
		var show_count: bool = copies > 1
		_count_label.text = str(copies) if show_count else ""
		if _count_badge != null:
			_count_badge.visible = show_count


func set_selected(value: bool) -> void:
	_selected = value
	if _select_badge != null:
		_select_badge.visible = value


func is_selected() -> bool:
	return _selected


## Grey the card out when the player cannot afford it.
func set_affordable(affordable: bool) -> void:
	modulate = Color(1, 1, 1, 1) if affordable else Color(0.55, 0.55, 0.62, 1)


func _on_gui_input(event: InputEvent) -> void:
	# TapInput, not a raw event check: on Android one physical tap arrives
	# TWICE (a real screen touch plus the mouse event Godot emulates from
	# it). Counting both made a tap select the card and immediately
	# deselect it, so the card hand was dead on a real phone.
	if TapInput.is_press(event):
		accept_event()
		card_pressed.emit(self)
