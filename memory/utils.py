class BOSSES:
    IUDEX_GUNDYR = 1037

class ANIMATIONS:
    LIGHT_ATTACK = [23030000, 23030010, 23030020, 23030500, 23034000, 23034010, 23034020, 23034500],
    DODGE = [27010, 10027010]
    ROLL = [27115]
    MOVE = [10020210, 10020110, 300020110, 300020210],
    HEAL = [50110, 50111, 50112],
    IDLE = [0, 10000000]

GUNDYR_ONE_HOT_ANIM = {
    "Attack3000": 0,
    "Attack3001": 1,
    "Attack3002": 2,
    "Attack3003": 3,
    "Attack3004": 4,
    "Attack3005": 5,
    "Attack3006": 6,
    "Attack3007": 7,
    "Attack3008": 8,
    "Attack3009": 9,
    "Attack3010": 10,
    "Attack3011": 11,
    "Attack3012": 12,
    "Attack3013": 13,
    "Attack3014": 14,
    "Attack3015": 15,
    "Attack3029": 16,
    "ThrowAttack0": 17,
    "Attack1500": 18,
    "SABreak": 19,
}

WORLD_CHR_MAN_PATTERN = b"\x48\x8B\x1D...\x04\x48\x8B\xF9\x48\x85\xDB..\x8B\x11\x85\xD2..\x8D"