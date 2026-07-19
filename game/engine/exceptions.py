class GameError(Exception):
    pass

class NotPlayerTurnError(GameError):
    pass

class CardNotInHandError(GameError):
    pass

class EmptyBankError(GameError):
    pass

class GameFinishedError(GameError):
    pass

class PlayerDisconnectError(GameError):
    pass

class InvalidSuitError(GameError):
    pass

class InvalidActionError(GameError):
    pass

class InvalidMoveError(GameError):
    pass
