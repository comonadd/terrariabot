import subprocess
from subprocess import STDOUT, Popen, PIPE, DEVNULL
import sys
from PIL import Image, ImageDraw
import socket
from threading import Thread
import struct
from enum import Enum
from dataclasses import dataclass, field
from typing import List
import zlib
import numpy as np
from PIL import Image
import random
import time
import win32gui
import win32ui
from ctypes import windll
import action_controller as ac
import keyboard
import copy
from logger import logger
import client
import random
import math
import numpy as np
from enum import IntEnum
import gym
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
from rl.agents import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
from gym import error, spaces
import copy
import argparse
import sys
from utils import screenshot_window, focus_on_window, process_main_window_name
import os
import threading
import pexpect
import pexpect.popen_spawn
import errno
import wexpect
from shutil import copyfile
import shutil
import pywinauto
import pyautogui
import pydirectinput
import signal

TERR_INTERFACE_INT_DUR = 0.5
tshock_root = "./TShock/TerrariaServerAPI/TerrariaServerAPI/bin/Debug"
exe_path = "{}/TerrariaServer.exe".format(tshock_root)
TRAINING_WORLD_PATH = 'C:/Users/Dmitry/Documents/My Games/Terraria/Worlds/AITRAININGWORLD.wld'
terraria_exe_path = "D:/SteamLibrary/steamapps/common/Terraria/Terraria.exe"

def orig_world_path(wp):
    return "{}.original".format(wp)

class TerrariaServerManager():
    proc = None
    world_path = None
    original_world_path = None
    editing_orig = False

    def __init__(self, world_path=TRAINING_WORLD_PATH, edit_orig=False):
        if not os.path.isfile(world_path):
            logger.error("No world file found at {}".format(world_path))
        self.world_path = world_path
        self.original_world_path = orig_world_path(world_path)
        if edit_orig:
            self.editing_orig = True
        self.cmd = [exe_path,
                    '-port', '7777',
                    '-players', '16',
                    '-pass', '',
                    '-world', self.world_path]

    def start_server(self):
        self.proc = Popen(self.cmd, stdout=DEVNULL)

    def kill(self):
        print('saving')
        self.proc.terminate()
        self.proc = None
        if self.editing_orig:
            # save original if set to edit it
            copyfile(self.world_path, self.original_world_path)

    def reload_orig_world(self):
        if os.path.isfile(self.original_world_path):
            # copy original world file into the working file
            copyfile(self.original_world_path, self.world_path)
        else:
            # copy running version to the original
            copyfile(self.world_path, self.original_world_path)

    def reset(self):
        # kill the server if running
        if self.proc is not None:
            self.kill()
        self.reload_orig_world()
        # start the server
        self.start_server()

def whatever():
    pygame.init()
    client = Client()
    client.run()
    scaling_factor = 24
    window = pygame.display.set_mode((VIEWPORT_WIDTH*scaling_factor, VIEWPORT_HEIGHT*scaling_factor))
    screen = pygame.Surface((VIEWPORT_WIDTH, VIEWPORT_HEIGHT))
    print("Here")

    # Focus terraria window
    utils.focus_on_window(TERRARIA_WINDOW_NAME)

    vhp = int(VIEWPORT_HEIGHT // 2)
    vwp = int(VIEWPORT_WIDTH // 2)
    rect_width = 2
    rect_height = 2
    print(vwp, vhp)

    try:
        while client.running:
            # print("Tick")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    client.running = False

            screen.fill((0, 0, 0))
            if client.player and client.player.spawned:
                client.player.tilex = int((client.player.posx + CHARACTER_WIDTH) // 16.0)
                client.player.tiley = int((client.player.posy + CHARACTER_HEIGHT) // 16.0)
                client.viewport_startx = client.player.tilex - vwp
                client.viewport_starty = client.player.tiley - vhp
                client.viewport_endx = client.player.tilex + vwp
                client.viewport_endy = client.player.tiley + vhp
                # client.print_current_state(screen)
                ptiley = client.player.tiley
                ptilex = client.player.tilex
                # logger.debug("rerendering with pos ({},{})".format(ptilex, ptiley))
                for screeny, yoffset in enumerate(range(-vhp, vhp + 1)):
                    absy = ptiley + yoffset
                    for screenx, xoffset in enumerate(range(-vwp, vwp + 1)):
                        absx = ptilex + xoffset
                        clr = color_for_tile(client.tiles[absy][absx])
                        pygame.draw.rect(screen, clr, (screenx, screeny, rect_width, rect_height))

            window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))
            pygame.display.flip()

            action_to_perform = random.choice(POSSIBLE_ACTIONS)
            # action_to_perform()

            # time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exiting...")
        client.running = False
        sys.exit(0)

INPUT_INTERVAL = 0.4

def player_control(key):
    keyboard.press(key)
    time.sleep(INPUT_INTERVAL)
    keyboard.release(key)

def player_move_up():
    player_control('w')

def player_move_down():
    player_control('s')

def player_move_left():
    player_control('a')

def player_move_right():
    player_control('d')

def player_jump():
    player_control('space')

class Action(IntEnum):
    # Up = 0
    # Down = 1
    Left = 0
    Right = 1
    # Jump = 2

def click_at(x, y, dur=TERR_INTERFACE_INT_DUR):
    pydirectinput.moveTo(x, y)
    pydirectinput.mouseDown()
    time.sleep(dur)
    pydirectinput.mouseUp()

def press_key(key):
    keyboard.press(key)
    time.sleep(TERR_INTERFACE_INT_DUR)
    keyboard.release(key)

def ia_join_first_ip_world():
    # click on the multiplayer button
    print("multiplayer")
    click_at(950, 355)
    # once again click on the "join by ip" button
    print("join by ip")
    click_at(950, 355)
    # choose a player
    print("choosing player")
    click_at(609, 613)
    click_at(609, 613)
    click_at(609, 613)
    # join server
    print("join server")
    click_at(959, 350)

def ia_join_single_world():
    # "single player"
    click_at(955, 300)
    # choose player
    click_at(609, 613)
    click_at(609, 613)
    # choose world
    click_at(613, 374)

class TerrariaEnv(gym.Env):
    K = 5
    ACTION_TO_FUN_MAPPING = {
        # Action.Up: player_move_up,
        # Action.Down: player_move_down,
        Action.Left: player_move_left,
        Action.Right: player_move_right,
        # Action.Jump: player_jump,
    }
    terraria_hwnd = None

    def __init__(self):
        self.action_space = spaces.Discrete(len(list(TerrariaEnv.ACTION_TO_FUN_MAPPING.keys())))
        self.prev_health = 160
        # self.state = np.array(list(state.values()))
        # self.client = client.Client()
        # self.client.run()
        self.server_manager = TerrariaServerManager()
        def on_got_window_name(window_hwnd):
            self.terraria_hwnd = window_hwnd
            focus_on_window(self.terraria_hwnd)
        process_main_window_name("Terraria.exe", on_got_window_name)

    def get_state(self):
        img = screenshot_window(self.terraria_hwnd)
        img.thumbnail([sys.maxsize, 128], Image.ANTIALIAS)
        # img.save("img.png")
        # sys.exit(0)
        pix = np.array(img)
        # res = cv2.resize(img, dsize=(54, 140), interpolation=cv2.INTER_CUBIC)
        # maybe downscale
        return pix

    def perform_action(self, action):
        # print("performing action: {}".format(action))
        TerrariaEnv.ACTION_TO_FUN_MAPPING[action]()

    def reset(self):
        # kill and restart server with the original map
        print("restarting server")
        self.server_manager.reset()
        time.sleep(4)
        self.client = client.Client()
        self.client.run()
        time.sleep(4)
        while True:
            if self.client.did_spawn():
                break
            time.sleep(0.1)
        # escape out of the "closed connection" thing
        print("pressing escape")
        press_key("escape")
        ia_join_first_ip_world()
        state = self.get_state()
        return state

    def render(self, mode='human'):
        # already rendered in the window
        pass
        # render(self.get_state())

    def step(self, action):
        self.perform_action(action)
        # update()
        state = self.get_state()
        prev_health = self.prev_health
        hp = self.client.get_player_health()
        reward = hp - prev_health
        self.prev_health = hp
        logger.debug("step(): {}, reward={}".format(action, reward))
        done = hp <= 0
        return state, reward, done, {}

    def clone_state(self):
        return copy.deepcopy(self.get_state())

    def restore_state(self, state_):
        # what to do here??
        print('restore_state()')
        # state = copy.deepcopy(self.get_state())

    def clone_full_state(self):
        return copy.deepcopy(self.get_state())

    def restore_full_state(self, state_):
        # global state
        # state = copy.deepcopy(state_)
        # how???
        pass

# Model
def setup_model(env):
    model = Sequential()
    actions_amount = env.action_space.n
    model.add(Flatten(input_shape=(1, 128, 228, 3)))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(actions_amount, activation='linear'))
    return model

def setup_agent(env, model):
    actions_amount = env.action_space.n
    policy = BoltzmannQPolicy()
    memory = SequentialMemory(limit=50000, window_length=1)
    dqn = DQNAgent(model=model, memory=memory, policy=policy,
                    nb_actions=actions_amount, nb_steps_warmup=10, target_model_update=1e-2)
    dqn.compile(Adam(lr=1e-3), metrics=['mae'])
    return dqn

MODEL_FILE = "pixel_model_weights.dqn"

def train():
    _env = TerrariaEnv()
    model = setup_model(env)
    dqn = setup_agent(env, model)
    dqn.fit(env, nb_steps=50000, visualize=False, verbose=1)
    dqn.save_weights(MODEL_FILE, overwrite=True)

def run_model():
    env = TerrariaEnv()
    model = setup_model(env)
    dqn = setup_agent(env, model)
    dqn.load_weights(MODEL_FILE)
    dqn.test(env, nb_episodes=50, visualize=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', action='store_true', default=False)
    parser.add_argument('--play', action='store_true', default=False)
    parser.add_argument('--edit-world', action='store_true', default=False)
    args = parser.parse_args()
    if args.train:
        print("Training")
        train()
    elif args.edit_world:
        print("Modifying original world")
        # s = TerrariaServerManager(edit_orig=True)
        # s.start_server()
        # s.reload_orig_world()
        # def signal_handler(sig, frame):
        #     s.kill()
        #     sys.exit(0)
        # signal.signal(signal.SIGINT, signal_handler)
        def on_got_window_name(window_hwnd):
            terraria_hwnd = window_hwnd
            focus_on_window(terraria_hwnd)
            op = orig_world_path(TRAINING_WORLD_PATH)
            if os.path.isfile(op):
                shutil.move(op, TRAINING_WORLD_PATH)
            ia_join_single_world()
        process_main_window_name("Terraria.exe", on_got_window_name)
        while True:
            time.sleep(1)
    else:
        print("Running saved model")
        run_model()
