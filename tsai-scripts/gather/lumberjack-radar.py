"""
Name: Tsai's Lumberjack Radar Assistant

** USER CONFIGURABLE OPTIONS ARE AT THE BOTTOM **

Description: Detects trees within 6 tiles and hues them.
  - Clicking the `Detect` button or `Q` hotkey will re-hue nearby trees and add them to the Radar
  - Clicking the button on the Radar will pathfind to and harvest the node
  - `E` hotkey will harvest the closest unharvested node (including Rich Trees)
- Other notable features
  - Automatically finds and equips hatchet from your backpack
  - Move Logs/Bark Fragments to a container (usually placed on a pack animal) when overweight
  - Can also stop execution by using War Mode
Author: Tsai (Ultima: Memento)
GitHub Source: Jascen/tazuo-scripts
Version: v1.2
"""


class OverweightBehavior:
    Stop = 0 # Stop the script
    Move = 1 # Move the boards/logs to a bag or pack animal


# Manual Configuration - Begin
# Logger.DEBUG = True
# Logger.TRACE = True
class UserOptions:
    Overweight_threshold = 60 # When your available weight is less than this value, execute Overweight behavior
    Overweight_behavior = OverweightBehavior.Move
    Clear_hands_before_move = False # In case you're a monk and need to access the rucksack
    Tree_To_Harvest_Hue = 1152
    Harvested_Tree_Hue = 1267

    HOTKEY__DETECT_NODES = "Q" # Use `None` to disable hotkey
    HOTKEY__HARVEST_CLOSEST = "E" # Use `None` to disable hotkey

    @staticmethod
    def get_ignored_tree_graphics():
        # You can add to this if it keeps trying to chop things it shouldn't
        return [
            3223,
            3230
        ]
# Manual Configuration - End

# import API

from tsai._gumps.radar import Radar
from tsai._models.generalitem import GeneralItem
from tsai._services.lumberjack import LumberjackService
from tsai._utils.alias import AliasUtils
from tsai._utils.logger import Logger
from tsai._utils.player import PlayerUtils


LumberjackSparkle = GeneralItem(0x373A, "a rich tree")


class LumberjackRadar(Radar):
    def __init__(self):
        Radar.__init__(self, self._get_nearby_trees)
        self.label = "Tsai's Lumberjacking Radar"
        self.ignored_tree_graphics = UserOptions.get_ignored_tree_graphics()
        self.move_destination = None


    def create_gump(self):
        super().create_gump(self.label)
        self.gump.CanCloseWithRightClick = False


    def harvest_closest_node(self):
        Logger.trace("[LumberjackRadar.harvest_closest_node]")
        try:
            # Sparkles count as a node
            if self._harvest_closest_sparkle():
                return

            radar_buttons = self.radar_buttons[:]
            radar_buttons.sort(key=lambda tree: tree.entity.Distance if tree.entity and tree.entity.Distance and tree.entity else 10000) # Large number

            for radar_button in radar_buttons:
                if radar_button.button.BackgroundHue == UserOptions.Tree_To_Harvest_Hue:
                    if radar_button.click_fn:
                        radar_button.click_fn()
                    return
        except Exception as e:
            Logger.error(str(repr(e)))
    
    
    def _harvest_closest_sparkle(self):
        Logger.trace("[LumberjackRadar._harvest_closest_sparkle]")
        items = API.GetItemsOnGround(10, LumberjackSparkle.graphic)
        if not items:
            return False

        for item in items:
            self.overweight_check()
            if not LumberjackService.ensure_hatchet():
                return
            
            LumberjackService.pathfind_to(item, 2)
            API.UseObject(item.Serial)
            API.Pause(1)
        
        return True


    def ensure_move_container(self):
        Logger.trace("[LumberjackRadar._ensure_move_container]")
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


    def overweight_check(self):
        Logger.trace("[LumberjackRadar.overweight_check]")
        if PlayerUtils.has_capacity(UserOptions.Overweight_threshold):
            return

        if UserOptions.Overweight_behavior == OverweightBehavior.Move:
            Logger.log("Overweight. Moving items!")
            LumberjackService.move_gathered(self.move_destination, UserOptions.Clear_hands_before_move)
        else:
            Logger.error("Overweight. Moving items!")
            API.Stop()


    def _get_nearby_trees(self):
        Logger.debug("[LumberjackRadar._get_nearby_trees]")
        for static in LumberjackService.filter_nearby_trees(self.radius, self.ignored_tree_graphics, UserOptions.Tree_To_Harvest_Hue, UserOptions.Harvested_Tree_Hue, self._mark_tree_processed, False):
            self._mark_tree_processed(static, False)


    def _harvest(self, tree, radar_button=None):
        Logger.debug("[LumberjackRadar._harvest]")
        self.overweight_check()
        if not LumberjackService.ensure_hatchet():
            return

        API.TrackingArrow(tree.X, tree.Y)
        if LumberjackService.harvest(tree):
            LumberjackService.hide_statics(tree, UserOptions.Harvested_Tree_Hue)
            if radar_button:
                radar_button.set_node_hue(UserOptions.Harvested_Tree_Hue)
            API.TrackingArrow(-1, -1)


    def _mark_tree_processed(self, static, hide=True):
        Logger.debug("[LumberjackRadar._mark_tree_processed]")

        x = static.X - API.Player.X
        y = static.Y - API.Player.Y
        for radar_button in self.radar_buttons:
            if x != radar_button.rel_x or y != radar_button.rel_y:
                continue

            # Track, mark, and make visible
            radar_button.set_entity(static)
            radar_button.set_node_hue(UserOptions.Harvested_Tree_Hue if static.Hue == UserOptions.Harvested_Tree_Hue else UserOptions.Tree_To_Harvest_Hue)
            radar_button.set_visible(True)
            radar_button.click_fn = lambda tree=static,button=radar_button: self._harvest(tree, button)

        if hide:
            LumberjackService.hide_statics(static, UserOptions.Harvested_Tree_Hue)


def main():
    radar = LumberjackRadar()
    radar.create_gump()
    radar.ensure_move_container()
    radar.overweight_check()

    if UserOptions.HOTKEY__DETECT_NODES:
        API.OnHotKey(UserOptions.HOTKEY__DETECT_NODES, radar.detect_nodes)
    if UserOptions.HOTKEY__HARVEST_CLOSEST:
        API.OnHotKey(UserOptions.HOTKEY__HARVEST_CLOSEST, radar.harvest_closest_node)
    
    player = API.Player
    while not API.StopRequested and not player.IsDead:
        radar.sync_position(player.X, player.Y)
        API.ProcessCallbacks()
        API.Pause(0.25)


main()