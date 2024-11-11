from enum import Enum
from abc import ABC, abstractmethod
from .Connection import Connection

class SwarmStatus(Enum):
    SEEDER = 0
    LEECHER = 1

class Swarm(ABC):
    def __init__(self, file_id: int, server_conn: Connection):
        self.file_id = file_id
        self.server_conn = server_conn

    @abstractmethod
    def get_status(self):
        """

        :return: Seeder or leecher status
        """
        pass

class SeederSwarm(Swarm):
    def __init__(self, file_id: int, server_conn: Connection):
        super().__init__(file_id, server_conn)

    def get_status(self):
        return SwarmStatus.SEEDER