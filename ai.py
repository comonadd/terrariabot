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
    SpawnAnswer = 12
    PlayerControls = 13
    CharacterHealth = 16
    TileEdit = 17
    BlockUpdate = 20
    ItemInfo = 21
    ItemOwnerInfo = 22
    NPCInfo = 23
    UpdateProjectile = 27
    DeleteProjectile = 29
    TogglePVP = 30
    PasswordRequest = 37
    PasswordAnswer = 38
    CharacterMana = 42
    JoinTeam = 45
    SpawnRequest = 49
    CharacterBuff = 50
    EvilRatio = 57
    DailyAnglerQuestFinished = 74
    ChatMessage = 82
    EightyThree = 83
    CharacterStealth = 84
    InventoryItemInfo = 89
    NinetySix = 96
    TowerShieldStrength = 101

    UnknownWhatever = 136

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

Color = List[int]

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


# Save world image into a file
def write_world_chunk_to_image(img, tiles, x_start, y_start, width, height):
    for y in range (y_start, y_start + height):
        for x in range (x_start, x_start + width):
            clr = (0, 0, 255) if tiles[y][x] is not None else None
            t = tiles[y][x]
            if t == None:
                clr = (255, 255, 0)
            elif t.tile_type == None:
                clr = (0, 0, 0)
            elif t.tile_type == 0:
                clr = (151, 107, 75)
            elif t.tile_type == 1:
                clr = (128, 128, 128)
            elif t.tile_type == 53:
                clr = (255, 218, 56)
            else:
                clr = (255,255,255)
            img.putpixel((x,y), clr)
    img.save('world_snapshot.png')

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
        print(self.world)
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
        print("Parsing tile data: x={},y={},width={},height={}".format(x_start,y_start,width,height))

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
        print('total tiles: {}'.format(len(self.tiles)))
        print('tile at x={}, y={} ::: {}'.format(SAND_X, SAND_Y, self.tile_at(SAND_X, SAND_Y)))

    def tile_at(x, y):
        return self.tiles[y][x]

    def read_socket(self):
        """ Reading messages loop """
        handlers = {
            MessageType.ChatMessage: self.ignore_packet, # this is not chat message
            MessageType.AuthentificationSuccess: self.auth_success,
            MessageType.FatalError: self.fatal_error,
            MessageType.WorldInfoAnswer: self.got_world_info,
            MessageType.TileData: self.got_tile_data,
            MessageType.EightyThree: self.ignore_packet,
            MessageType.RecalculateUV: self.ignore_packet,
            MessageType.ItemInfo: self.ignore_packet,
            MessageType.ItemOwnerInfo: self.ignore_packet,
            MessageType.NPCInfo: self.ignore_packet,
            MessageType.SpawnRequest: self.ignore_packet,
            MessageType.Status: self.ignore_packet,
        }
        while self.running:
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
            msg_type_typed = MessageType(msg_type)
            handler = handlers.get(msg_type_typed, None)
            if handler is None:
                print("No handler for messages of type {}".format(msg_type_typed))
                continue
            handler(data)

    def write_socket(self):
        """ Writing messages loop """
        while self.running:
            if len(self.write_queue) > 0:
                # Pop the message out of the write queue and send it
                msg = self.write_queue[0]
                self.write_queue.pop(0)
                send_msg(self.sock, msg)

    def add_message(self, msg):
        self.write_queue.append(msg)

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
        self.add_message(ConnectionMessage())
        try:
            while self.running:
                pass
        except KeyboardInterrupt:
            print("Exiting...")
            self.running = False
            sys.exit(0)


def run():
    client = Client()
    client.run()

if __name__ == "__main__":
    run()
