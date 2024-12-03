
class DownloadFileException(Exception):
    def __init__(self, message):
        self.message = message

class SwarmException(Exception):
    def __init__(self, message):
        self.message = message

class ServerConnectionError(Exception):
    def __init__(self, message):
        self.message = message

class ProgramTerminateException(Exception):
    def __init__(self, message):
        self.message = message