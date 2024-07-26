from enum import Enum

class Tracks(Enum):
    track1: str='Boat Operators'
    track2: str='Motorola Radios'
    track3: str='Test Director'
    track4: str='Patrol Craft Command Unit (PCCU)'

track_mapping = {k.name:k.value for k in Tracks}