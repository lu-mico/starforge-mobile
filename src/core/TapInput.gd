class_name TapInput
extends RefCounted
## TapInput — tells a REAL press apart from the mouse event Godot emulates
## from a touch.
##
## On Android ONE physical tap reaches the engine TWICE. Measured on a real
## device (2026-10-29, Medium_Phone_API_36.1), the card's `gui_input` fired
## four times for one finger-down:
##
##   1. InputEventMouseButton  (device -1, pressed)  <- emulated from touch
##   2. InputEventScreenTouch  (device  0, pressed)  <- the real finger
##   3. InputEventMouseButton  (device -1, released)
##   4. InputEventScreenTouch  (device  0, released)
##
## `input_devices/pointing/emulate_mouse_from_touch` is ON by default, so
## BOTH arrive. A handler that accepts both counts one tap as TWO presses:
## the card hand selected itself and then immediately deselected itself, so
## the whole deploy flow was dead on a phone — while every headless gate
## stayed green, because the headless harness pushes a single synthetic
## event and never sees the pair.
##
## THE RULE: an emulated mouse event is the shadow of a touch that was
## already delivered as a screen touch. Ignore it. A REAL mouse (desktop,
## editor, or a wired mouse on the tablet) reports device 0 and is never
## ignored, so desktop behaviour is unchanged.

## The device id Godot stamps on an event it generated itself.
const EMULATED_DEVICE := -1


## True when `event` is a press the player actually made.
##
## One physical tap on Android yields exactly one true: the screen touch.
## The emulated mouse twin of that same tap is rejected. On desktop a real
## mouse click is accepted exactly once.
static func is_press(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.device == EMULATED_DEVICE:
			return false
		return mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT
	if event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		return st.pressed
	return false


## True when `event` is a release the player actually made.
static func is_release(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.device == EMULATED_DEVICE:
			return false
		return not mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT
	if event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		return not st.pressed
	return false


## True when the event came from a finger rather than a mouse.
static func is_touch(event: InputEvent) -> bool:
	return event is InputEventScreenTouch
