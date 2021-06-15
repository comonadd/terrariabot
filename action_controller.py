import keyboard
import time

ACTION_DURATION = 0.2

def move_right():
    keyboard.press('d')
    time.sleep(ACTION_DURATION)
    keyboard.release('d')

def move_left():
    keyboard.press('a')
    time.sleep(ACTION_DURATION)
    keyboard.release('a')

def jump():
    keyboard.press('space')
    time.sleep(ACTION_DURATION)
    keyboard.release('space')
