

class SwarmException(Exception):
    def __init__(self, message):
        self.message = message

class ServerConnectionError(Exception):
    def __init__(self, message):
        self.message = message