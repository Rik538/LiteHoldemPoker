# -*- coding: utf-8 -*-
"""
Created on Sun May 17 17:31:43 2026

@author: Richard
"""

from .evaluate_hand import EvaluateHand

class Showdown():
    
    def __init__(self):
        self.E = EvaluateHand()
    
    def resolve_showdown(self,p0_private,p1_private,public,pot):
        
        result = self.resolve_hands(p0_private, p1_private, public)
        
        if result is None:
            return (pot/2,pot/2)
        
        elif result == 1:
            return (0,pot)
        
        else:
            return (pot,0)
            
        
    
    def resolve_hands(self,p0_private,p1_private,public):
        p0_hand = self.E.evaluate(p0_private, public)
        p1_hand = self.E.evaluate(p1_private, public)
        
        if p0_hand > p1_hand: return 0 
        
        if p1_hand > p0_hand: return 1
        
        return None
    

            
        
        