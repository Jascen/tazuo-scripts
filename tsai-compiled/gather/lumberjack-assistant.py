"""
Name: Lumerjack Assistant
Description: Attempts to completely lumberjack every tree around you.
    Overweight behavior is configurable.
Author: Tsai (Ultima: Memento)
GitHub Source: Jascen/tazuo-scripts
Version: v1.4.1
"""

# import API

class OverweightBehavior:
    Stop = 0 # Stop the script
    Move = 1 # Move the boards/logs to a bag or pack animal


# Manual Configuration - Begin
class UserOptions:
    Overweight_Threshold = 60 # When your available weight is less than this value, execute Overweight behavior
    Overweight_Behavior = OverweightBehavior.Move
    Max_Retries = 3 # Default to 15
    Clear_hands_before_move = False # Memento: In case you're a monk and need to access the rucksack
    Radius_Hue = 0 # Set to `0` to disable
    Tree_To_Harvest_Hue = 1152
    Harvested_Tree_Hue = 1267
    
    # If your server converts Logs to Boards by axeing them, you can enable this
    Axe_Logs_Before_Moving_Items = False
    Axe_Logs_After_When_Moving_Items = False

    Enable_Diagnostic_Logging = False

    @staticmethod
    def get_ignored_tree_graphics():
        # You can add to this if it keeps trying to chop things it shouldn't
        return [
            3223,
        ]
    
    @staticmethod
    def apply_corrections():
        # If your shard requires modifications, place them here

        # Update
        # Log.graphic = 0x1BDD
        # Board.graphic = 0x0
        # Hatchet.graphic = 0x0

        LumberjackService.lazy_initialize()

        # LumberjackService.Stump_graphic = 0x0
        pass
# Manual Configuration - End


# import API

# import API

class Hue:
    LightPink = 31
    LightPurple = 16
    Orange = 43
    Red = 33

class Logger:
    DEBUG = False
    TRACE = False

    TraceColor = Hue.LightPink
    DebugColor = Hue.LightPurple
    InfoColor = Hue.Orange
    ErrorColor = Hue.Red

    @classmethod
    def trace(cls, message):
        if not Logger.TRACE: return
        API.SysMsg("[trace]: " + message, cls.TraceColor)

    @classmethod
    def debug(cls, message):
        if not Logger.DEBUG: return
        API.SysMsg("[debug]: " + message, cls.DebugColor)

    @classmethod
    def error(cls, message):
        API.SysMsg("[error]: " + message, cls.ErrorColor)

    @classmethod
    def log(cls, message):
        API.SysMsg(message, cls.InfoColor)
# import API


class PlayerUtils:
    @staticmethod
    def clear_hands():
        if API.FindLayer("TwoHanded"):
            API.Pause(1)
            API.ClearLeftHand()
        if API.FindLayer("OneHanded"):
            API.Pause(1)
            API.ClearLeftHand()


    @staticmethod
    def has_capacity(weight_required):
        available = API.Player.WeightMax - API.Player.Weight

        return weight_required <= available
class GeneralItem:
    """Basic details for a single type of item"""
    def __init__(self, graphic, name, hue = -1):
        self.graphic = graphic
        self.name = name
        self.hue = hue


# Resources
Board          = GeneralItem(7127, "board")
Ingot          = GeneralItem(7154, "ingot")
Leather        = GeneralItem(4225, "leather")
Log            = GeneralItem(7136, "log")
BarkFragment   = GeneralItem(12687, "bark fragment")

# Tools
Hatchet        = GeneralItem(3907, "hatchet")


class LumberjackService:
    Types_to_move = None
    Stump_graphic = None


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


    @staticmethod
    def ensure_hatchet():
        Logger.trace("[LumberjackService.ensure_hatchet]")

        while not API.Player.IsDead:
            if API.FindLayer("TwoHanded"):
                Logger.trace("Found item in hand")
                item = API.FindItem(API.Found)
                if item and item.Graphic == Hatchet.graphic:
                    return True

                Logger.trace("Item was not a Hatchet")

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
            if (static.IsTree or (not ignore_stumps and static.Graphic == cls.Stump_graphic)) \
                and static.Graphic not in ignored_graphics:
                trees.append(static)

        return trees


    @staticmethod
    def harvest(tree, auto_pathfind=True, min_distance=2):
        Logger.trace("[LumberjackService.harvest]")
        
        if not API.FindLayer("TwoHanded"):
            Logger.debug("No axe was found")
            return False

        item = API.FindItem(API.Found)

        if item.Graphic != Hatchet.graphic:
            # Something else is in the hand
            Logger.error("Item in hand is not a Hatchet!")
            API.Pause(0.5)
            return False
        
        tree = tree
        if min_distance < tree.Distance:
            if not auto_pathfind:
                Logger.error("Too far and pathfinding was disabled.")
                return False
            
            Logger.debug("Too far. Pathfinding to tree.")
            API.Pathfind(tree.X, tree.Y, tree.Z, min_distance)
            while API.Pathfinding():
                API.Pause(0.25)
        
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
                
                API.QueueMoveItem(serial, destination)
                API.IgnoreObject(serial)
                #API.Pause(0.750)
# import API


class AliasUtils:
    @classmethod
    def get_value(cls, alias, scope):
        """Gets the value for the `alias`"""
        value = API.GetPersistentVar(alias, "", scope)

        return value if value else None


    @classmethod
    def get_value_or_default(cls, alias, scope, default):
        """Gets the value or the default"""
        return API.GetPersistentVar(alias, default, scope)


    @classmethod
    def get_value_or_prompt(cls, alias, scope, prompt_message, timeout=30):
        """Gets the Serial for the `alias` or prompts if it is not found"""
        value = cls.get_value(alias, scope)

        return value if value else cls.prompt(alias, scope, prompt_message, timeout)


    @classmethod
    def prompt(cls, alias, scope, prompt_message, timeout=30):
        """Prompts the user to set a value for the alias"""
        serial = cls.get_value(alias, scope)
        if not serial:
            API.SysMsg(prompt_message)
            serial = API.RequestTarget(timeout)
            if not serial: return None

            API.SavePersistentVar(alias, str(serial), scope)

        return serial


    # @classmethod
    # def CreateCharacterAlias(cls, alias, force = False):
    #     """Returns an alias that is pre-pended with the character name"""
    #     name = Engine.Player.Name.strip() # Sometimes there's a leading/trailing space
    #     if not force and alias.startswith(name): return alias # Assume it was already formatted

    #     return "{}-{}".format(name, alias)


    # @classmethod
    # def EnsureContainer(cls, alias, prepend = True):
    #     """Searches for the `alias` and prompts if it is not found or it is a mobile"""
    #     if prepend: alias = cls.CreateCharacterAlias(alias)
    #     if FindAlias(alias):
    #         backpack = cls.GetBackpackSerial(alias)
    #         if backpack != None: SetMacroAlias(alias, backpack)
    #         return alias

    #     return cls.PromptContainer(alias, False)


    # @classmethod
    # def PromptContainer(cls, alias, scope, prompt_message, timeout=30):
    #     """Prompts the user for the target and attempts to set the alias value to the mobile's Backpack"""
    #     PromptMacroAlias(alias)

    #     backpack = cls.GetBackpackSerial(alias)
    #     if backpack != None:
    #         SetMacroAlias(alias, backpack)

    #     return alias


    # @classmethod
    # def IsMobile(cls, alias):
    #     """Returns `True` if the serial of the alias is in the range for Mobiles"""
    #     return UOMath.IsMobile(alias)


    # @classmethod
    # def GetBackpackSerial(cls, alias):
    #     """Attempts to return the Backpack of the mobile"""
    #     serial = GetAlias(alias)
    #     if cls.IsMobile(serial):
    #         mobile = Engine.Mobiles.GetMobile(serial)
    #         if mobile and mobile.Backpack: return mobile.Backpack # Set the backpack if it exists
    #     # TODO: If it's not a Container ... good luck. Tough determining if it's a Container
        
    #     return None
# import API



class ScriptUtils:
    def check_auto_pause():
        while API.Player.IsDead or API.Player.InWarMode:
            if API.Player.InWarMode:
                Logger.log("Script is paused due to war mode")
            API.Pause(1)


class LumberjackAssistant:
    def __init__(self):
        self.move_destination = None


    def ensure_move_container(self):
        Logger.trace("[LumberjackAssistant._ensure_move_container]")
        if UserOptions.Overweight_Behavior != OverweightBehavior.Move or self.move_destination:
            return
        
        bag = AliasUtils.get_value_or_prompt("$wood_bag", API.PersistentVar.Char, "Target a container for your logs.")
        if not bag:
            Logger.error("No bag was specified.")
            return

        serial = int(bag)
        bag_item = API.FindItem(serial)
        if not bag_item:
            Logger.error("Failed to find storage bag.")
            return
        
        if UserOptions.Enable_Diagnostic_Logging:
            API.SysMsg(f"Your overweight container: {bag_item.Name} ({bag_item.Serial})")
        
        self.move_destination = serial


    def harvest_around_you(self):
        Logger.debug("[LumberjackAssistant.harvest_around_you]")
        self.ensure_move_container()

        radius = 2
        if UserOptions.Radius_Hue:
            API.DisplayRange(radius, UserOptions.Radius_Hue)
        else:
            API.DisplayRange(0)

        hide_harvested = lambda t: LumberjackService.hide_statics(t, UserOptions.Harvested_Tree_Hue) if t.Hue == UserOptions.Harvested_Tree_Hue else None
        trees = LumberjackService.filter_nearby_trees(radius, UserOptions.get_ignored_tree_graphics(), UserOptions.Tree_To_Harvest_Hue, UserOptions.Harvested_Tree_Hue, hide_harvested)

        trees_remaining = len(trees)
        for index, tree in enumerate(trees):
            if 0 < trees_remaining - index:
                API.HeadMsg("{} trees remaining".format(trees_remaining - index), API.Player, 33)
            API.TrackingArrow(tree.X, tree.Y)
            self._clean_it_out(tree)
            API.TrackingArrow(-1, -1)


    def overweight_check(self):
        Logger.trace("[LumberjackAssistant.overweight_check]")

        if PlayerUtils.has_capacity(UserOptions.Overweight_Threshold):
            return

        if UserOptions.Axe_Logs_Before_Moving_Items:
            self._chop_logs()
            if PlayerUtils.has_capacity(UserOptions.Overweight_Threshold):
                return

        if UserOptions.Axe_Logs_After_When_Moving_Items:
            self._chop_logs()

        if UserOptions.Overweight_Behavior == OverweightBehavior.Move:
            Logger.debug("Overweight. Moving items!")
            LumberjackService.move_gathered(self.move_destination, UserOptions.Clear_hands_before_move, UserOptions.Enable_Diagnostic_Logging)
        else:
            Logger.error("Overweight. Moving items!")
            API.Stop()


    def _chop_logs(self):
        Logger.debug("[LumberjackAssistant._chop_logs]")
        # This method is not required for Memento. It is included as a convenience for other servers

        #Look for hatchet
        if not LumberjackService.ensure_hatchet():
            return
        
        item = API.FindItem(API.Found)
        if item.Graphic != Hatchet.graphic:
            # Something else is in the hand
            API.HeadMsg("Need a hatchet in hand!", API.Player, 33)
            API.Pause(1)
            return

        while API.FindType(Log.graphic, API.Backpack):
            API.CancelTarget()
            API.UseObject(item.Serial)
            if API.WaitForTarget("any", 1):
                API.Target(API.Found)
                API.Pause(1)


    def _clean_it_out(self, tree):
        Logger.debug("[LumberjackAssistant._clean_it_out]")
        API.ClearJournal()
        
        attempt = 0
        while not API.Player.IsDead:
            ScriptUtils.check_auto_pause()

            if (2 < abs(API.Player.X - tree.X)
                or 2 < abs(API.Player.Y - tree.Y)):
                API.HeadMsg("Tree too far!", API.Player, 33)
                API.Pause(1)
                continue

            # Memento automatically executes the next swing
            if API.InJournal("You chop some", True) or API.InJournal("You hack at", True):
                API.ClearJournal()
                API.Pause(0.5)
                continue

            attempt += 1
            self._harvest(tree)
            API.Pause(1)

            self.overweight_check()
            
            # Move when there is nothing left
            if API.InJournal("There's not enough wood here to harvest.", True):
                return 1 < attempt

            if attempt == UserOptions.Max_Retries:
                # Bail idk why we can't hit anything
                return 1 < attempt


    def _harvest(self, tree):
        Logger.debug("[LumberjackAssistant._harvest]")
        if not LumberjackService.ensure_hatchet():
            return

        if LumberjackService.harvest(tree, False):
            LumberjackService.hide_statics(tree, UserOptions.Harvested_Tree_Hue)


def Main():
    UserOptions.apply_corrections()
    assistant = LumberjackAssistant()
    assistant.ensure_move_container()
    assistant.overweight_check()
    assistant.harvest_around_you()
    API.HeadMsg("Complete", API.Player, 33)

# Execute Main
Main()
