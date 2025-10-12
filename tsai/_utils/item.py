# import API

from tsai._utils.logger import Logger


class ItemUtils:
    @staticmethod
    def PromptForType(message):
        """Prompts the User to select an item and returns the Graphic ID"""
        while not API.StopRequested:
            Logger.Log(message)
            serial = API.RequestTargget()
            if not serial:
                continue

            item = API.FindItem(serial)
            if not item:
                continue

            return item.Graphic