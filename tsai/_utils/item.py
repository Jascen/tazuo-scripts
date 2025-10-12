# import API

from tsai._utils.logger import Logger


class ItemUtils:
    # @classmethod
    # def GetAll(cls, graphic, hue, distance, source_serial_or_alias):
    #     items = []
    #     while FindType(graphic, distance, source_serial_or_alias, hue):
    #         items.append(GetAlias("found"))
    #         IgnoreObject("found")
        
    #     return items


    @staticmethod
    def PromptForType(message):
        """Prompts the User to select an item and returns the Graphic ID"""
        while not API.StopRequested:
            Logger.log(message)
            serial = API.RequestTargget()
            if not serial:
                continue

            item = API.FindItem(serial)
            if not item:
                continue

            return item.Graphic


    # @classmethod
    # def Move(cls, graphic, hue, distance, source_serial_or_alias, destination, ignore_destination_first = False):
    #     """Moves the items to the destination container"""
    #     if ignore_destination_first:
    #         while API.FindType(graphic, destination):
    #             API.IgnoreObject(API.Found)

    #     cls.__Move(graphic, hue, distance, source_serial_or_alias, lambda item: MoveItem(item, destination))


    # @classmethod
    # def MoveToOffset(cls, graphic, hue, distance, source_serial_or_alias, x, y, z):
    #     """Moves the items to the ground offset position"""
    #     cls.__Move(graphic, hue, distance, source_serial_or_alias, lambda item: MoveItemOffset(item, x, y, z))


    # @classmethod
    # def __Move(cls, graphic, hue, distance, source_serial_or_alias, move_fn):
    #     items = cls.GetAll(graphic, hue, distance, source_serial_or_alias)
                
    #     for item in items:
    #         move_fn(item)
    #         Pause(750)