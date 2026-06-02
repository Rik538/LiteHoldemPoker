# -*- coding: utf-8 -*-
"""
Created on Sun May 31 17:06:48 2026

@author: Richard
"""

from enum import Enum, auto

class Action(Enum):
    FOLD = auto()
    CHECK_CALL = auto()
    BET_RAISE = auto()
    
