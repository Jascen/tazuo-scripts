"""
Name: Lumerjack Assistant
Description: Attempts to completely lumberjack every tree around you.
    Overweight behavior is configurable.
Author: Tsai (Ultima: Memento)
Version: v1.4
"""

import API

from tsai._services.lumberjack import LumberjackService
from tsai._utils.alias import AliasUtils
from tsai._utils.logger import Logger
from tsai._utils.player import PlayerUtils
from tsai._utils.script import ScriptUtils


class LumberjackAssistant:
    def __init__(self):
        self.move_destination = None


    def harvest_around_you(self):
        Logger.debug("[LumberjackAssistant.harvest_around_you]")
        self._ensure_move_container()

        radius = 2
        if UserOptions.Radius_Hue:
            API.DisplayRange(radius, UserOptions.Radius_Hue)
        else:
            API.DisplayRange(0)

        hide_harvested = lambda t: LumberjackService.hide_statics(tree, UserOptions.Harvested_Tree_Hue) if t.Hue == UserOptions.Harvested_Tree_Hue else None
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
        if PlayerUtils.has_capacity(UserOptions.Overweight_threshold):
            return

        if UserOptions.Overweight_behavior == OverweightBehavior.Move:
            Logger.debug("Overweight. Moving items!")
            LumberjackService.move_gathered(self.move_destination, UserOptions.Clear_hands_before_move)
        else:
            Logger.error("Overweight. Moving items!")
            API.Stop()


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

            if attempt == UserOptions.Max_retries:
                # Bail idk why we can't hit anything
                return 1 < attempt


    def _ensure_move_container(self):
        Logger.trace("[LumberjackAssistant._ensure_move_container]")
        if UserOptions.Overweight_behavior != OverweightBehavior.Move or self.move_destination:
            return
        
        bag = AliasUtils.get_value_or_prompt("$wood_bag", API.PersistentVar.Char, "Target a container for your logs.")
        if not bag:
            Logger.error("No bag was specified.")
            return

        serial = int(bag)
        if not API.FindItem(serial):
            Logger.error("Failed to find storage bag.")
            return
        
        self.move_destination = serial


    def _harvest(self, tree):
        Logger.debug("[LumberjackAssistant._harvest]")
        if not LumberjackService.ensure_hatchet():
            return

        if LumberjackService.harvest(tree, False):
            LumberjackService.hide_statics(tree, UserOptions.Harvested_Tree_Hue)


def Main():    
    assistant = LumberjackAssistant()
    assistant.overweight_check()
    assistant.harvest_around_you()
    API.HeadMsg("Complete", API.Player, 33)


class OverweightBehavior:
    Stop = 0 # Stop the script
    Move = 1 # Move the boards/logs to a bag or pack animal


# Manual Configuration - Begin
class UserOptions:
    Overweight_threshold = 60 # When your available weight is less than this value, execute Overweight behavior
    Overweight_behavior = OverweightBehavior.Move
    Max_retries = 3 # Default to 15
    Clear_hands_before_move = False # In case you're a monk and need to access the rucksack
    Radius_Hue = 1260 # Set to `0` to disable
    Tree_To_Harvest_Hue = 1152
    Harvested_Tree_Hue = 1

    @staticmethod
    def get_ignored_tree_graphics():
        # You can add to this if it keeps trying to chop things it shouldn't
        return [
            3223,
        ]
# Manual Configuration - End

# Execute Main
Main()