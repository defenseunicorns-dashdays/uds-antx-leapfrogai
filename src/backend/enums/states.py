from enum import Enum

class States(Enum):
    TRIAL_START='Trial Start'
    TRIAL_END='Trial End'
    DELAY_START='Delay Start'
    DELAY_END='Delay End'
    MISTRIAL='Mistrial'
    RTB='RTB'
