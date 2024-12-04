from enum import Enum
from abc import ABC, abstractmethod
from .Connection import Connection

class SwarmStatus(Enum):
    SEEDER = 0
    LEECHER = 1

class Swarm(ABC):
    def __init__(self, file_id: int, server_conn: Connection, file_name: str):
        self.file_id = file_id
        self.server_conn = server_conn
        self.file_name = file_name

    @abstractmethod
    def get_status(self):
        """

        :return: Seeder or leecher status
        """
        pass

class SeederSwarm(Swarm):
    def __init__(self, file_id: int, server_conn: Connection, file_name: str):
        super().__init__(file_id, server_conn, file_name)

    def get_status(self):
        return SwarmStatus.SEEDER