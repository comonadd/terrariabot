import subprocess
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
import pygame

# Tiles for which the frame is considered "important".
TILE_FRAME_IMPORTANT = [
    False, False, False, True, True, True, False, False, False, False, True, True, True, True,
    True, True, True, True, True, True, True, True, False, False, True, False, True, True, True,
    True, False, True, False, True, True, True, True, False, False, False, False, False, True,
    False, False, False, False, False, False, True, True, False, False, False, False, True, False,
    False, False, False, False, True, False, False, False, False, False, False, False, False,
    False, True, True, True, True, False, False, True, True, True, False, True, True, True, True,
    True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True,
    True, True, True, True, True, True, False, False, False, True, False, False, True, True, False,
    False, False, False, False, False, False, False, False, False, True, True, False, True, True,
    False, False, True, True, True, True, True, True, True, True, False, True, True, True, True,
    False, False, False, False, True, False, False, False, False, False, False, False, False,
    False, False, False, False, False, False, False, True, False, False, False, False, False, True,
    True, True, True, False, False, False, True, False, False, False, False, False, True, True,
    True, True, False, False, False, False, False, False, False, False, False, False, False, False,
    False, True, False, False, False, False, False, True, False, True, True, False, True, False,
    False, True, True, True, True, True, True, False, False, False, False, False, False, True,
    True, False, False, True, False, True, False, True, True, True, True, True, True, True, True,
    True, True, True, True, True, False, False, False, False, False, False, True, False, False,
    False, False, False, False, False, False, False, False, False, False, False, False, True, True,
    True, False, False, False, True, True, True, True, True, True, True, True, True, False, True,
    True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True,
    True, True, True, True, True, True, True, True, True, False, False, False, True, False, True,
    True, True, True, True, False, False, True, True, False, False, False, False, False, False,
    False, False, False, True, True, False, True, True, True, False, False, False, False, False,
    False, False, False, False, True, False, False, False, False, True, True, True, False, True,
    True, True, True, True, True, True, False, False, False, False, False, False, False, True,
    True, True, True, True, True, True, False, True, False, False, False, False, False, True, True,
    True, True, True, True, True, True, True, True, False, False, False, False, False, False,
    False, False, False, True, True, False, False, False, True, True, True, True, True, False,
    False, False, False, True, True, False, False, True, True, True, False, True, True, True,
    False, False, False, False, False, False, False, False, False, False, True, True, True, True,
    True, True, False, False, False, False, False, False, True, True, True, True, True, True,
    False, False, False, True, True, True, True, True, True, True, True, True, True, True, False,
    False, False, True, True, False, False, False, True, False, False, False, True, True, True,
    True, True, True, True, True, False, True, True, False, False, True, False, True, False, False,
    False, False, False, True, True, False, False, True, True, True, False, False, False, False,
    False, False, True, True, True, True, True, True, True, True, True, True, False, True, True,
    True, True, True, False, False, False, False, True, False, False, False, True, True, True,
    True, False, True, True, True, True, True, True, True, True, True, True, False, True, True,
    True, False, False, False, True, True, False, True, True, True, True, True, True, True, False,
    False, False, False, False, True, True, True, True, True, True, True, True, True, True, True,
    True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True,
    True, True, True, True, True, True, True, True, True, True, True, True, False, True, True,
    True, True,
]

VIEWPORT_WIDTH = 20
VIEWPORT_HEIGHT = VIEWPORT_WIDTH
NETWORK_RW_INTERVAL = 0.01

TileType = int

@dataclass
class Tile:
    tile_type: TileType
    frame: List[int]
    tile_color: int

class Streamer:
    """A class for streaming data from a databuffer."""

    def __init__(self, data):
        self.data = data
        self.index = 0

    def next_short(self):
        result = struct.unpack("<h", self.data[self.index: self.index + 2])[0]
        self.index += 2
        return result

    def next_u_short(self):
        result = struct.unpack("<H", self.data[self.index: self.index + 2])[0]
        self.index += 2
        return result

    def next_int32(self):
        result = struct.unpack("<i", self.data[self.index: self.index + 4])[0]
        self.index += 4
        return result

    def next_byte(self):
        result = self.data[self.index]
        self.index += 1
        return result

    def next_float(self):
        result = struct.unpack("<f", self.data[self.index: self.index + 4])[0]
        self.index += 4
        return result

    def remainder(self):
        return self.data[self.index:]

VERSION = 238
# VERSION = 100

class MessageType(Enum):
    Authentification = 1
    FatalError = 2
    AuthentificationSuccess = 3
    CharacterCreation = 4
    CharacterInventorySlot = 5
    WorldInfoRequest = 6
    WorldInfoAnswer = 7
    InitialTileRequest = 8
    Status = 9
    TileData = 10
    RecalculateUV = 11
    SpawnRequest = 12
    PlayerControls = 13

    PlayerActive = 14 # Should probably react to this

    CharacterHealth = 16
    TileEdit = 17
    BlockUpdate = 20
    ItemInfo = 21
    ItemOwnerInfo = 22
    NPCInfo = 23
    UpdateProjectile = 27
    DeleteProjectile = 29
    TogglePVP = 30

    PlayerZone = 36

    PasswordRequest = 37

    ThirtyNine = 39  # ??? Remove ItemOwner I guess

    SetActiveNPC = 40

    PasswordAnswer = 38
    CharacterMana = 42
    JoinTeam = 45
    SpawnSuccessAnswer = 49
    CharacterBuff = 50
    EvilRatio = 57

    NPCHomeUpdate = 60

    DailyAnglerQuestFinished = 74

    SyncPlayerChestIndex = 80

    ChatMessage = 82
    EightyThree = 83
    CharacterStealth = 84
    InventoryItemInfo = 89
    NinetySix = 96

    NotifyPlayerOfEvent = 98

    TowerShieldStrength = 101

    MoonLordCountdown = 103

    PlayerHurtV2 = 117

    SyncTilePicking = 125
    FinishedConnectingToServer  = 129
    UnknownWhatever = 136
    SetCountsAsHostForGameplay = 139


def msg_data_add_byte(b, d):
    b += struct.pack('<b', d)
    return b

def msg_data_add_str(b, s):
    s_bytes = bytes(s, 'utf-8')
    b += struct.pack('<b', len(s))
    b += s_bytes
    return b

def msg_data_add_short(b, s):
    b += struct.pack('<h', s)
    return b

def msg_data_add_int32(b, i):
    b += struct.pack('<i', i)
    return b

def msg_data_add_float(b, f):
    b += struct.pack('<f', f)
    return b

Color = List[int]

CHARACTER_HEIGHT = 48.0

def tile_coord_to_pos(coord):
    return coord * 16.0

@dataclass
class Player:
    slot_num: int
    name: str
    hair_color: Color = field(default_factory=lambda: [0, 0, 0])
    skin_color: Color = field(default_factory=lambda: [0, 0, 0])
    eyeColor: Color = field(default_factory=lambda: [0, 0, 0])
    shirtColor: Color = field(default_factory=lambda: [0, 0, 0])
    undershirtColor: Color  = field(default_factory=lambda: [0, 0, 0])
    pantsColor: Color = field(default_factory=lambda: [0, 0, 0])
    shoeColor: Color = field(default_factory=lambda: [0, 0, 0])
    difficulty: int = 0

    hp: int = 200
    max_hp: int = 200

    mana: int = 200
    max_mana: int = 200

    spawned: bool = False
    posx: float = 0.0
    posy: float = 0.0
    velocity_x: float = 1.0
    velocity_y: float = 1.0

class ConnectionMessage:
    _type = MessageType.Authentification
    def to_bytes(self):
        b = bytes()
        version_str = "Terraria" + str(VERSION)
        b = msg_data_add_str(b, version_str)
        return b

@dataclass
class PlayerInfo:
    # Packet number 4
    """ Client -> Server. Send character information, such as skin, hairstyle, etc. """
    player: Player
    _type = MessageType.CharacterCreation
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # slot num
        b = msg_data_add_byte(b, 4)  # Skin
        b = msg_data_add_byte(b, 0)
        b = msg_data_add_str(b, self.player.name)
        b = msg_data_add_byte(b,0)  # HairStyle
        b = msg_data_add_byte(b,1)  # HideVisual?
        b = msg_data_add_byte(b,1)  # HideVisual2?
        b = msg_data_add_byte(b,0)  # Hide miscs

        b = msg_data_add_byte(b, self.player.hair_color[0])
        b = msg_data_add_byte(b, self.player.hair_color[1])
        b = msg_data_add_byte(b, self.player.hair_color[2])

        b = msg_data_add_byte(b, self.player.skin_color[0])
        b = msg_data_add_byte(b, self.player.skin_color[1])
        b = msg_data_add_byte(b, self.player.skin_color[2])

        b = msg_data_add_byte(b, self.player.eyeColor[0])
        b = msg_data_add_byte(b, self.player.eyeColor[1])
        b = msg_data_add_byte(b, self.player.eyeColor[2])

        b = msg_data_add_byte(b, self.player.shirtColor[0])
        b = msg_data_add_byte(b, self.player.shirtColor[1])
        b = msg_data_add_byte(b, self.player.shirtColor[2])

        b = msg_data_add_byte(b, self.player.undershirtColor[0])
        b = msg_data_add_byte(b, self.player.undershirtColor[1])
        b = msg_data_add_byte(b, self.player.undershirtColor[2])

        b = msg_data_add_byte(b, self.player.pantsColor[0])
        b = msg_data_add_byte(b, self.player.pantsColor[1])
        b = msg_data_add_byte(b, self.player.pantsColor[2])

        b = msg_data_add_byte(b, self.player.shoeColor[0])
        b = msg_data_add_byte(b, self.player.shoeColor[1])
        b = msg_data_add_byte(b, self.player.shoeColor[2])

        b = msg_data_add_byte(b, self.player.difficulty)

        return b


@dataclass
class PlayerHPInfo:
    # Packet number 16
    """ Client <-> Server. Send character health info """
    player: Player
    _type = MessageType.CharacterHealth
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # player id
        b = msg_data_add_short(b, self.player.hp)
        b = msg_data_add_short(b, self.player.max_hp)
        return b

@dataclass
class PlayerManaInfo:
    """ Client <-> Server. Send character mana info """
    player: Player
    _type = MessageType.CharacterMana
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # player id
        b = msg_data_add_short(b, self.player.mana)
        b = msg_data_add_short(b, self.player.max_mana)
        return b

@dataclass
class PlayerBuffState:
    """ Client <-> Server. Send character buff table: Array of 22 shorts """
    player: Player
    _type = MessageType.CharacterBuff
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # player id
        PLAYER_BUFF_STATE_SIZE = 22
        for i in range(PLAYER_BUFF_STATE_SIZE):
            b = msg_data_add_short(b, 0)
        return b

@dataclass
class PlayerInventorySlot:
    """ Client <-> Server. Information about the inventory slot at Nth position
0 - 58 = Inventory, 59 - 78 = Armor, 79 - 88 = Dye, 89 - 93 MiscEquips, 94 - 98 = MiscDyes, 99 - 138 = Piggy bank, 139 - 178 = Safe, 179 = Trash, 180 - 219 = Defender's Forge, 220 - 259 = Void Vault
"""
    player: Player
    inv_slot: int
    stack: int
    prefix: int
    item_id: int
    _type = MessageType.CharacterInventorySlot
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # player id
        b = msg_data_add_short(b, self.inv_slot) # inventory slot id
        b = msg_data_add_short(b, self.stack) # stack size
        b = msg_data_add_byte(b, self.prefix) # prefix???
        b = msg_data_add_short(b, self.item_id) # item NET id
        return b

class RequestWorldData:
    """ Client -> Server. Request world data """
    _type = MessageType.WorldInfoRequest
    def to_bytes(self):
        b = bytes()
        return b

@dataclass
class RequestEssentialTiles:
    """ Client -> Server """
    _type = MessageType.InitialTileRequest
    player_spawn_x: int
    player_spawn_y: int
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_int32(b, self.player_spawn_x)
        b = msg_data_add_int32(b, self.player_spawn_y)
        return b

@dataclass
class SpawnPlayer:
    """ Client -> Server """
    _type = MessageType.SpawnRequest
    player: Player
    player_spawn_x: int
    player_spawn_y: int
    respawn_time_rem: int
    spawn_context: int
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # player id
        b = msg_data_add_short(b, self.player_spawn_x)
        b = msg_data_add_short(b, self.player_spawn_y)
        b = msg_data_add_int32(b, self.respawn_time_rem)
        b = msg_data_add_byte(b, self.spawn_context)
        return b

UPDATE_VELOCITY = 0x04
@dataclass
class PlayerControl:
    """ Client <-> Server """
    _type = MessageType.PlayerControls
    player: Player
    control_flag: int
    def to_bytes(self):
        b = bytes()
        b = msg_data_add_byte(b, self.player.slot_num) # player id

        b = msg_data_add_byte(b, self.control_flag) # control action byte

        pulley_flags = UPDATE_VELOCITY
        b = msg_data_add_byte(b, pulley_flags) # pulley byte

        b = msg_data_add_byte(b, 0) # misc byte

        b = msg_data_add_byte(b, 0) # is sleeping
        b = msg_data_add_byte(b, 0) # selected item

        b = msg_data_add_float(b, self.player.posx) # posx
        b = msg_data_add_float(b, self.player.posy) # posx

        if pulley_flags & UPDATE_VELOCITY:
            b = msg_data_add_float(b, self.player.velocity_x) # velocity x
            b = msg_data_add_float(b, self.player.velocity_y) # velocity y

        # print(self.control_flag, self.player.posx, self.player.posy)

        return b

def send_msg(socket, msg):
    msg_data = msg.to_bytes()
    msg_len = len(msg_data)
    packet = struct.pack("<h", msg_len + 3)
    packet += struct.pack('b', msg._type.value)
    packet += msg_data
    total_sent = 0
    bytes_to_send = len(packet)
    while total_sent < bytes_to_send:
        sent = socket.send(packet[total_sent:])
        if sent == 0:
            raise RuntimeError("Socket connection broken")
        total_sent += sent


TERRARIA_EXEC_PATH = 'D:\SteamLibrary\steamapps\common\Terraria\Terraria.exe'

class World:
    time: int
    daynight: int
    moonphase: int
    max_x: int
    max_y: int
    spawn_x: int
    spawn_y: int

class LiquidType(Enum):
    Water = 1
    Lava = 2
    Honey = 3


MIN_TILE_TYPE   = -100
MAX_TILE_TYPE   = 1000
MAX_COLOR_VALUE = 255
def color_for_tile(t):
    if t is None or t.tile_type is None:
        return (0, 0, 0)
    tt = int((((t.tile_type - MIN_TILE_TYPE) * MAX_COLOR_VALUE) / (MAX_TILE_TYPE - MIN_TILE_TYPE)))
    # print(t.tile_type, tt)
    return (tt, tt, tt)

# Save world image into a file
def write_world_chunk_to_image(img, tiles, x_start, y_start, width, height):
    for y in range (y_start, y_start + height):
        for x in range (x_start, x_start + width):
            clr = color_for_tile(tiles[y][x])
            img.putpixel((x,y), clr)
    img.save('world_snapshot.png')

CONTROL_LEFT = 0x04
CONTROL_RIGHT = 0x08
CONTROL_JUMP = 0x10
POSSIBLE_ACTIONS = [CONTROL_JUMP, CONTROL_LEFT, CONTROL_RIGHT]

class Client:
    running = False
    # Messages to be written to the server
    write_queue = []
    # Main communication channel
    sock = None
    # Player
    player: Player = None
    # World
    world: World = None
    tiles: List[Tile] = []

    def stop(self):
        print('stopping')
        self.running = False

    def handle_chat_message(self, msg):
        print('got chat message??: {}'.format(msg))

    def ignore_packet(self, msg):
        pass

    def auth_success(self, msg):
        """
        The server sends this message when the connection is successful.
        It also sends the client's assigned player slot.
        All connected players are assigned a slot, 0-254.
        """
        slot_num = ord(msg[1:2])
        print("auth success: slot_num={}".format(slot_num))
        self.player = Player(slot_num, "AIBOT1")
        # Send information about the player to the server
        self.add_message(PlayerInfo(self.player))
        self.add_message(PlayerHPInfo(self.player))
        self.add_message(PlayerManaInfo(self.player))
        self.add_message(PlayerBuffState(self.player))
        # Initialize player inventory
        INV_SIZE = 259
        for inv_slot in range(INV_SIZE):
            stack = 0
            prefix = 0
            item_id = 0
            self.add_message(PlayerInventorySlot(self.player, inv_slot, stack, prefix, item_id))
        # Request world data
        self.add_message(RequestWorldData())

    def fatal_error(self, msg):
        print("fatal error: {}".format(msg))

    def got_world_info(self, msg):
        streamer = Streamer(msg)
        streamer.next_byte()  # Ignore packet ID byte
        self.world = World()
        self.world.time = streamer.next_int32()
        self.world.daynight = streamer.next_byte()
        self.world.moonphase = streamer.next_byte()
        self.world.max_x = streamer.next_short()
        self.world.max_y = streamer.next_short()
        self.world.spawn_x = streamer.next_short()
        self.world.spawn_y = streamer.next_short()
        # TODO: Parse remaining information
        # Log in
        self.add_message(SpawnPlayer(self.player, self.world.spawn_x, self.world.spawn_y,
                                     0, # respawn time remaining
                                     1  # Player Spawn Context	Byte
                                        # Enum: 0 = ReviveFromDeath,
                                        # 1 = SpawningIntoWorld,
                                        # 2 = RecallFromItem
                                     ))
        # Request essential tiles
        self.add_message(RequestEssentialTiles(self.world.spawn_x, self.world.spawn_y))
        self.tiles = np.empty([self.world.max_y, self.world.max_x], dtype=Tile)
        self.newImg1 = Image.new('RGB', (self.world.max_x,self.world.max_y), (255, 255, 255))

    def got_tile_data(self, msg):
        streamer = Streamer(msg)
        streamer.next_byte()  # Ignore packet ID byte
        is_compressed = streamer.next_byte()
        if is_compressed:
            compressed_data = streamer.remainder()
            data = zlib.decompress(compressed_data, -zlib.MAX_WBITS)
            streamer = Streamer(data)
        x_start = streamer.next_int32()
        y_start = streamer.next_int32()
        width = streamer.next_short()
        height = streamer.next_short()
        # print("Parsing tile data: x={},y={},width={},height={}".format(x_start,y_start,width,height))

        # Read actual tile data
        rle = 0
        SAND_X = 1911
        SAND_Y = 274
        for y in range(y_start, y_start + height):
            for x in range(x_start, x_start + width):
                # print(x, y)
                # If there are tiles to repeat
                if rle != 0:
                    # TODO: Maybe make a copy
                    self.tiles[y][x] = prev_tile
                    rle -= 1
                    continue
                flag1 = streamer.next_byte()
                flag2 = 0
                flag3 = 0
                if flag1 & 0x01 != 0:
                    flag2 = streamer.next_byte()
                    if flag2 & 0x01 != 0:
                        flag3 = streamer.next_byte()
                tile_type = None
                frame = None
                tile_color = None
                if flag1 & 0x02 != 0:
                    tile_type = streamer.next_short() if flag1 & 0x20 != 0 else streamer.next_byte()
                    if tile_type > 0 and tile_type < len(TILE_FRAME_IMPORTANT) and TILE_FRAME_IMPORTANT[tile_type]:
                        frame = [streamer.next_short(), streamer.next_short()]
                    else:
                        frame = None
                    tile_color = streamer.next_byte() if flag1 & 0x08 != 0 else None
                else:
                    tile_type = None
                    frame = None
                    tile_color = None
                # wall
                wall = None
                if flag1 & 0x04 != 0:
                    wall = streamer.next_byte()
                    if flag3 & 0x10 != 0:
                        wall = [wall, streamer.next_byte()]
                    else:
                        wall = [wall, None]
                # liquid
                liquid = None
                liquid_f = (flag1 & 0x18) >> 3
                if liquid_f in LiquidType._value2member_map_:
                    liquid = LiquidType(liquid_f)
                    liquid_amount = streamer.next_byte()
                # wire
                wire = [
                    flag2 & 0x02 != 0,
                    flag2 & 0x04 != 0,
                    flag2 & 0x08 != 0,
                    flag2 & 0x20 != 0,
                ]

                # TODO: Parse these properly
                # shape = flags[1] & 0x70 >> 4;
                # half_brick = shape == 1;
                # slope = if shape > 1 { shape - 1 } else { 0 };
                # actuator = flags[2] & 0x02 != 0;
                # inactive = flags[2] & 0x04 != 0;
                # if flags[2] & 0x40 != 0 {
                #     // this flag basically sets the higher byte of the u16
                #     wall.as_mut().expect("wall should be present").0 |= (cursor.read::<u8>() as u16) << 8;
                # }

                rle = (flag1 & 0xc0) >> 6
                if rle == 0:
                    rle = 0
                elif rle == 1:
                    rle = streamer.next_byte()
                else:
                    rle = streamer.next_short()

                t = Tile(tile_type, frame, tile_color)
                self.tiles[y][x] = t
                prev_tile = t
        # print('total tiles: {}'.format(len(self.tiles)))
        # print('tile at x={}, y={} ::: {}'.format(SAND_X, SAND_Y, self.tile_at(SAND_X, SAND_Y)))

    def tile_at(self, x, y):
        return self.tiles[y][x]

    def update_character_health(self, msg):
        streamer = Streamer(msg)
        streamer.next_byte()
        player_id = streamer.next_byte()
        # Ignore other players heatlh update
        # if player_id != self.player.slot_num:
            # return
        self.player.hp = streamer.next_short()
        self.player.max_hp = streamer.next_short()
        # print('Update player health. Now hp={}, max_hp={}'.format(self.player.hp, self.player.max_hp))

    def on_successfull_spawn(self, msg):
        self.player.spawned = True
        self.player.posx = tile_coord_to_pos(self.world.spawn_x)
        self.player.posy = tile_coord_to_pos(self.world.spawn_y) - CHARACTER_HEIGHT

    def sync_spectator_pos_with_target(self):
        pass
        # self.add_message(PlayerControl(self.player, 0))

    def server_player_control_update(self, msg):
        streamer = Streamer(msg)
        streamer.next_byte()

        player_id = streamer.next_byte()

        # Ignore if other player's position updated
        # if player_id != self.player.slot_num:
            # return

        streamer.next_byte() # control
        pulley = streamer.next_byte() # pulley
        streamer.next_byte() # misc

        streamer.next_byte() # sleeping
        streamer.next_byte() # selected item

        posx = streamer.next_float() # posx
        posy = streamer.next_float() # posy

        velocity_x = 0.0
        velocity_y = 0.0
        if pulley & UPDATE_VELOCITY:
            velocity_x = streamer.next_float()
            velocity_y = streamer.next_float()

        # print('updting player pos to x={},y={}, velocity is ({}, {})'.format(
            # posx, posy, velocity_x, velocity_y))

        self.player.posx = posx
        self.player.posy = posy
        self.player.velocity_x = velocity_x
        self.player.velocity_y = velocity_y

        # let original_and_home_pos = if misc & 0x40 != 0 {
        #     Some((cursor.read(), cursor.read()))
        # } else {
        #     None
        # };

    def read_socket(self):
        """ Reading messages loop """
        handlers = {
            MessageType.ChatMessage: self.ignore_packet, # this is not chat message
            MessageType.AuthentificationSuccess: self.auth_success,
            MessageType.FatalError: self.fatal_error,
            MessageType.WorldInfoAnswer: self.got_world_info,
            MessageType.TileData: self.got_tile_data,
            MessageType.SpawnSuccessAnswer: self.on_successfull_spawn,
            MessageType.PlayerControls: self.server_player_control_update,

            MessageType.PlayerActive: self.ignore_packet,
            MessageType.CharacterCreation: self.ignore_packet,
            MessageType.TogglePVP: self.ignore_packet,
            MessageType.JoinTeam: self.ignore_packet,
            MessageType.SyncPlayerChestIndex: self.ignore_packet,
            MessageType.NPCHomeUpdate: self.ignore_packet,
            MessageType.DailyAnglerQuestFinished: self.ignore_packet,
            MessageType.SetActiveNPC: self.ignore_packet,
            MessageType.PlayerZone: self.ignore_packet,

            MessageType.EightyThree: self.ignore_packet,
            MessageType.RecalculateUV: self.ignore_packet,
            MessageType.ItemInfo: self.ignore_packet,
            MessageType.ItemOwnerInfo: self.ignore_packet,
            MessageType.NPCInfo: self.ignore_packet,
            MessageType.Status: self.ignore_packet,

            MessageType.CharacterInventorySlot: self.ignore_packet,
            MessageType.EvilRatio: self.ignore_packet,

            MessageType.UpdateProjectile: self.ignore_packet,
            MessageType.DeleteProjectile: self.ignore_packet,

            MessageType.ThirtyNine: self.ignore_packet,
            MessageType.UnknownWhatever: self.ignore_packet,

            MessageType.TileEdit: self.ignore_packet,
            MessageType.BlockUpdate: self.ignore_packet,

            MessageType.CharacterHealth: self.update_character_health,
            MessageType.CharacterMana: self.ignore_packet, # Should probably sync
            MessageType.CharacterBuff: self.ignore_packet, # Should probably sync

            MessageType.MoonLordCountdown: self.ignore_packet,
            MessageType.TowerShieldStrength: self.ignore_packet,
        }
        while self.running:
            # print("receiving")
            packet_length = self.sock.recv(2)
            if len(packet_length) < 2:
                self.stop()
                continue
            # -2 because we don't consider the short length number to be a part of the data
            packet_length = struct.unpack('<h', packet_length)[0] - 2
            if packet_length <= 0:
                print("length is zero")
                continue
            data = self.sock.recv(packet_length)
            msg_type = data[0]
            if msg_type not in MessageType._value2member_map_:
                print("Warning: msg_type #{} isn't present in MessageType enum".format(msg_type))
                continue
            msg_type_typed = MessageType(msg_type)
            handler = handlers.get(msg_type_typed, None)
            if handler is None:
                print("No handler for messages of type {}".format(msg_type_typed))
                continue
            handler(data)
            time.sleep(NETWORK_RW_INTERVAL)
            # print("done sleeping")

    def write_socket(self):
        """ Writing messages loop """
        while self.running:
            if len(self.write_queue) > 0:
                # Pop the message out of the write queue and send it
                msg = self.write_queue[0]
                self.write_queue.pop(0)
                send_msg(self.sock, msg)
            time.sleep(NETWORK_RW_INTERVAL)

    def add_message(self, msg):
        self.write_queue.append(msg)

    def print_current_state(self, screen):
        if self.player is not None and self.player.spawned:
            print("\tPlayer: x={},y={},tilex={},tiley={},vel=({},{})".format(
                self.player.posx,
                self.player.posy,
                self.player.tilex,
                self.player.tiley,
                self.player.velocity_x,
                self.player.velocity_y))
            print("\t        hp={},mana={}".format(self.player.hp, self.player.mana))

    def random_action(self):
        while self.running:
            if self.player is not None and self.player.spawned:
                self.sync_spectator_pos_with_target()
            time.sleep(1)
        #         # print("Sending random action")
        #         action_msg = PlayerControl(
        #             self.player,
        #             random.choice(POSSIBLE_ACTIONS)
        #         )
        #         self.add_message(action_msg)

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", 7777))
        self.running = True
        read_thread = Thread(target=self.read_socket)
        read_thread.daemon = True
        read_thread.start()
        write_thread = Thread(target=self.write_socket)
        write_thread.daemon = True
        write_thread.start()

        player_thread = Thread(target=self.random_action)
        player_thread.daemon = True
        player_thread.start()

        self.add_message(ConnectionMessage())

TERRARIA_WINDOW_NAME = "Terraria: I don't know that-- aaaaa!"

def screenshot_terraria_window():
    hwnd = win32gui.FindWindow(None, TERRARIA_WINDOW_NAME)

    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #left, top, right, bot = win32gui.GetClientRect(hwnd)
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area.
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
    print (result)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    if result == 1:
        #PrintWindow Succeeded
        return im
        # im.save("test.png")

def main():
    pygame.init()
    client = Client()
    client.run()
    scaling_factor = 24
    window = pygame.display.set_mode((VIEWPORT_WIDTH*scaling_factor, VIEWPORT_HEIGHT*scaling_factor))
    screen = pygame.Surface((VIEWPORT_WIDTH, VIEWPORT_HEIGHT))
    print("Here")
    try:
        while client.running:
            # print("Tick")
            client.player.tilex = client.player.posx // 16.0
            client.player.tiley = (client.player.posy + CHARACTER_HEIGHT) // 16.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    client.running = False

            screen.fill((0, 0, 0))
            if client.player and client.player.spawned:
                client.print_current_state(screen)
                viewport_startx = int(client.player.tilex - VIEWPORT_WIDTH)
                viewport_starty = int(client.player.tiley - VIEWPORT_HEIGHT)
                rect_width = 2
                rect_height = 2
                for y in range(0, VIEWPORT_HEIGHT):
                    for x in range(0, VIEWPORT_WIDTH):
                        realy = y + viewport_starty
                        realx = x + viewport_startx
                        clr = color_for_tile(client.tiles[realy][realx])
                        pygame.draw.rect(screen, clr, (x, y, rect_width, rect_height))

            window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))
            pygame.display.flip()
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exiting...")
        client.running = False
        sys.exit(0)

if __name__ == "__main__":
    main()
