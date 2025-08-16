from dataclasses import dataclass

@dataclass
class Globals:
    """Klasa przechowująca globalne zmienne i stałe aplikacji"""

    GLOBAL_ULID = "01K16YDK7GNRBANHHQDMZVRGE7"  # Stały ULID dla globalnych operacji
    AGENT_UID = "00000000-0000-0000-0000-LUX:AGENT"  # Stały UID dla agenta
    AGENT_NAME = "LUX Agent"  # Nazwa agenta
    AGENT_DESCRIPTION = "LUX Agent - zarządza interakcjami i relacjami w świecie LUX"  # Opis agenta

    @staticmethod
    def get_world_uid():
        return Globals.WORLD_UID

    @staticmethod
    def get_agent_uid():
        return Globals.AGENT_UID

    @staticmethod
    def get_agent_name():
        return Globals.AGENT_NAME

    @staticmethod
    def get_agent_description():
        return Globals.AGENT_DESCRIPTION