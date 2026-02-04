from enum import Enum

class GameState(Enum):
    MENU = "menu"
    SETTINGS = "settings"
    SHOP = "shop"
    GAME = "game"
    VICTORY = "victory"
    GAME_OVER = "game_over"

class Element(Enum):
    NONE = 0
    EAU = 1
    TERRE = 2
    AIR = 3
    FEU = 4

class Direction(Enum):
    DOWN = 0
    UP = 1
    LEFT = 2
    RIGHT = 3
