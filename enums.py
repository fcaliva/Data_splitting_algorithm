from enum import Enum, IntEnum
from functools import lru_cache


class Side(IntEnum):
    Left = 0
    Right = 1


class TimePoint(IntEnum):
    V0 = 0
    V1 = 1
    V3 = 3
    V5 = 5
    V6 = 6
    V8 = 8
    V10 = 10


class Race(IntEnum):
    unknown = -1
    other = 0
    white = 1
    black = 2
    asian = 3


class Gender(IntEnum):
    unknown = 0
    male = 1
    female = 2


class TKR(IntEnum):
    no = 0
    yes = 1