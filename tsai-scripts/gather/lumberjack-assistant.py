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


from tsai._services.lumberjack import LumberjackService
from tsai._entities.generalitem import Log, Hatchet, Board
from tsai._utils.alias import AliasUtils
from tsai._utils.logger import Logger
from tsai._utils.player import PlayerUtils
from tsai._utils.script import ScriptUtils


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