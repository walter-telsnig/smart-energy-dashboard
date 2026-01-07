from datetime import datetime, date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class PatternType(str, Enum):
    """Types of energy usage patterns"""
    WEEKDAY_WARRIOR = "weekday_warrior"      
    WEEKEND_WARRIOR = "weekend_warrior"  
    NIGHT_OWL = "night_owl"                  
    MORNING_BIRD = "morning_bird"            
    DAYTIME_USER = "daytime_user"            
    EVENING_PEAKER = "evening_peaker"        
    CONSISTENT_USER = "consistent_user"     
    VARIABLE_USER = "variable_user"       
    SOLAR_ALIGNED = "solar_aligned"          
    SOLAR_MISALIGNED = "solar_misaligned"    

