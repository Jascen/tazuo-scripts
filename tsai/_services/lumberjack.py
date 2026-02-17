# import API

from tsai._utils.logger import Logger
from tsai._utils.player import PlayerUtils
from tsai._entities.generalitem import Hatchet, Log, BarkFragment, Board


class LumberjackService:
    Types_to_move = None
    Stump_graphic = None
    Paperdoll_Hatchet_Graphics = None


    @classmethod
    def lazy_initialize(cls):
        if cls.Types_to_move:
            return

        cls.Types_to_move = [
            Log.graphic,
            BarkFragment.graphic,
            Board.graphic
        ]
        cls.Stump_graphic = 0x0E59
        cls.Paperdoll_Hatchet_Graphics = [
            Hatchet.graphic,
            25747, # Monster hatchet graphic
        ]


    @classmethod
    def is_hatchet_in_hand(cls):
        Logger.trace("[LumberjackService.is_hatchet_in_hand]")

        if API.FindLayer("TwoHanded"):
            Logger.trace("Found item in hand")
            item = API.FindItem(API.Found)
            if item and item.Graphic in cls.Paperdoll_Hatchet_Graphics:
                return True

            Logger.trace("Item was not a Hatchet")

        return False


    @classmethod
    def ensure_hatchet(cls):
        Logger.trace("[LumberjackService.ensure_hatchet]")

        while not API.Player.IsDead:
            if cls.is_hatchet_in_hand():
                return True

            found = API.FindType(Hatchet.graphic, API.Backpack)
            if found:
                Logger.trace("Found a Hatchet")
                PlayerUtils.clear_hands()

                API.Pause(1) # In case an action previously executed
                API.EquipItem(found)
                continue

            Logger.error("Failed to find a Hatchet in backpack")
            API.Pause(.25)

        return False


    @classmethod
    def filter_nearby_trees(cls, radius, ignored_graphics, to_process_hue, processed_tree_hue, processed_tree_fn, ignore_stumps=True):
        Logger.debug("[LumberjackService.filter_nearby_trees]")
        trees = []

        for tree in cls.get_nearby_trees(radius, ignored_graphics, ignore_stumps):
            if tree.Hue == processed_tree_hue:
                if processed_tree_fn:
                    processed_tree_fn(tree)
            else:
                tree.SetHue(to_process_hue)
                trees.append(tree)

        return trees


    @classmethod
    def get_nearby_trees(cls, radius, ignored_graphics, ignore_stumps=True):
        cls.lazy_initialize()

        Logger.debug("[LumberjackService.get_nearby_trees]")
        trees = []
        statics = API.GetStaticsInArea(API.Player.X - radius, API.Player.Y - radius, API.Player.X + radius, API.Player.Y + radius)
        
        for static in statics:
            if cls.is_valid_tree(static, ignored_graphics, ignore_stumps):
                trees.append(static)

        return trees


    @classmethod
    def is_valid_tree(cls, static, ignored_graphics, ignore_stumps=True):
        cls.lazy_initialize()

        Logger.trace("[LumberjackService.is_valid_tree]")
        return (static.IsTree or (not ignore_stumps and static.Graphic == cls.Stump_graphic)) \
            and static.Graphic not in ignored_graphics


    @staticmethod
    def pathfind_to(tree, min_distance):
        Logger.trace("Too far. Pathfinding to tree.")
        API.Pathfind(tree.X, tree.Y, tree.Z, min_distance)
        while API.Pathfinding():
            API.Pause(0.25)


    @classmethod
    def harvest(cls, tree, auto_pathfind=True, min_distance=2):
        Logger.trace("[LumberjackService.harvest]")

        if not cls.is_hatchet_in_hand():
            Logger.debug("No axe was found in hand")
            API.Pause(0.5)
            return False
        
        if min_distance < tree.Distance:
            if not auto_pathfind:
                Logger.error("Too far and pathfinding was disabled.")
                return False
            
            cls.pathfind_to(tree, min_distance)
        
        API.Pause(1)
        API.UseObject(API.Found)

        if API.WaitForTarget("any", 1):
            Logger.debug(f"Targeting tree ({tree.Graphic}) at {tree.X}, {tree.Y}, {tree.Z}")
            API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)
            return True

        Logger.error("Failed to get cursor target.")
        return False
    

    @classmethod
    def hide_statics(cls, tree, hue, graphic=None):
        cls.lazy_initialize()

        Logger.trace("[LumberjackAssistant.hide_statics]")
        for static in API.GetStaticsAt(tree.X, tree.Y):
            static.SetHue(hue)
            static.Graphic = graphic if graphic != None else cls.Stump_graphic


    @classmethod
    def move_gathered(cls, destination, clear_hands_before_move, log_every_move=False):
        cls.lazy_initialize()

        Logger.debug("[LumberjackService.move_gathered]")

        for type_id in cls.Types_to_move:
            if log_every_move:
                Logger.log(f"Looking to move type ({type_id})")

            # Ignore any already in the destination
            API.ClearIgnoreList()
            while API.FindType(type_id, destination):
                API.IgnoreObject(API.Found)
            
            if clear_hands_before_move:
                PlayerUtils.clear_hands()

            # Move to destination
            API.Pause(1) # In case an action previously executed
            while API.FindType(type_id, API.Backpack):
                serial = API.Found
                if log_every_move:
                    Logger.log(f"Moving ({serial}) to {destination}")
                
                API.QueueMoveItem(serial, destination, 9999)
                API.IgnoreObject(serial)
                #API.Pause(0.750)