from dataclasses import dataclass

@dataclass
class GameOptions:
    jack_blocks_takeit: bool = False   # R31
    two_wildcard:       bool = False   # R32
    allow_reconnect:    bool = True
