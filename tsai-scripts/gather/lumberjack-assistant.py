"""
Name: Lumerjack Assistant
Description: Attempts to completely lumberjack every tree around you.
    Overweight behavior is configurable.
Author: Tsai (Ultima: Memento)
Version: v1.2
"""

import API


DEBUG = False

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
    def GetIgnoredTreeGraphics():
        # You can add to this if it keeps trying to chop things it shouldn't
        return [
            3223,
        ]
# Manual Configuration - End

class Ids:
    log_id = 7136
    hatchet_id = 3907
    bark_fragment_id = 12687
    stump_id = 0x0E59


class Serials:
    move_destination = None # Set later


Items_to_move = [
    Ids.log_id, 
    Ids.bark_fragment_id
]


def CheckForPause():
    while API.Player.IsDead or API.Player.InWarMode: 
        API.Pause(1)


def EnsureHatchet():
    while not API.Player.IsDead:
        if API.FindLayer("TwoHanded"): return True

        if API.FindType(Ids.hatchet_id, API.Backpack):
            API.EquipItem(API.Found)
            continue

        API.HeadMsg("Failed to find Hatchet", API.Player, 33)
        API.Pause(1)

    return False


def GetNearbyTrees(radius, ignored_graphics):
    trees = []
    statics = API.GetStaticsInArea(API.Player.X - radius, API.Player.Y - radius, API.Player.X + radius, API.Player.Y + radius)
    
    raw_trees = []
    for static in statics:
        if static.IsTree and static.Graphic not in ignored_graphics:
            raw_trees.append(static)

    for tree in raw_trees:
        if tree.Hue != UserOptions.Harvested_Tree_Hue:
            tree.SetHue(UserOptions.Tree_To_Harvest_Hue)
            trees.append(tree)
        else:
            HideStatics(tree.X, tree.Y)

    return trees


def HideStatics(x, y):
    for static in API.GetStaticsAt(x, y):
        static.SetHue(UserOptions.Harvested_Tree_Hue)
        static.Graphic = Ids.stump_id


def MoveType(type_id):    
    # Ignore any already in the destination
    API.ClearIgnoreList()
    while API.FindType(type_id, Serials.move_destination):
        API.IgnoreObject(API.Found)
    
    API.Pause(1) # In case an action previously executed

    # Move to destination
    while API.FindType(type_id, API.Backpack):
        serial = API.Found
        if UserOptions.Clear_hands_before_move:
            if API.FindLayer("TwoHanded"):
                API.ClearLeftHand()
                API.Pause(1)
            if API.FindLayer("OneHanded"):
                API.ClearLeftHand()
                API.Pause(1)
        
        API.QueueMoveItem(serial, Serials.move_destination)
        API.IgnoreObject(serial)
        #API.Pause(0.750)


def Harvest(tree):
    #Look for hatchet
    if not EnsureHatchet():
        return
    
    item = API.FindItem(API.Found)
    if item.Graphic != Ids.hatchet_id:
        # Something else is in the hand
        API.HeadMsg("Need a hatchet in hand!", API.Player, 33)
        API.Pause(1)
        return
    
    API.Pause(1)
    API.UseObject(API.Found)
    if API.WaitForTarget("any", 1):
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)
        HideStatics(tree.X, tree.Y)


def HarvestAroundYou():
    OverweightCheck()

    radius = 2
    if UserOptions.Radius_Hue:
        API.DisplayRange(radius, UserOptions.Radius_Hue)
    else:
        API.DisplayRange(0)

    trees = GetNearbyTrees(radius, UserOptions.GetIgnoredTreeGraphics())
    
    trees_remaining = len(trees)
    for index, tree in enumerate(trees):
        if 0 < trees_remaining - index:
            API.HeadMsg("{} trees remaining".format(trees_remaining - index), API.Player, 33)
        API.TrackingArrow(tree.X, tree.Y)
        CleanItOut(tree)
        API.TrackingArrow(-1, -1)


def CleanItOut(tree):
    API.ClearJournal()
    
    attempt = 0
    while not API.Player.IsDead:
        CheckForPause()
        if (2 < abs(API.Player.X - tree.X)
            or 2 < abs(API.Player.Y - tree.Y)):
            API.HeadMsg("Tree too far!", API.Player, 33)
            API.Pause(1)
            continue

        # Memento automatically executes the next swing
        if API.InJournal("You chop some") or API.InJournal("You hack at"):
            API.ClearJournal()
            API.Pause(0.5)
            continue

        attempt += 1
        Harvest(tree)
        API.Pause(1)

        OverweightCheck()
        
        # Move when there is nothing left
        if API.InJournal("There's not enough wood here to harvest.", True):
            return 1 < attempt

        if attempt == UserOptions.Max_retries:
            # Bail idk why we can't hit anything
            return 1 < attempt


def DiffWeight():
    return API.Player.WeightMax - API.Player.Weight


def OverweightCheck():
    if DiffWeight() < UserOptions.Overweight_threshold:
        if UserOptions.Overweight_behavior == OverweightBehavior.Move:
            if DEBUG: API.SysMsg("Overweight. Moving items!")
            for type in Items_to_move:
                MoveType(type)
        else:
            API.SysMsg("Overweight. Stopping!")
            API.Stop()


def Main():
    if UserOptions.Overweight_behavior == OverweightBehavior.Move:
        bag = API.GetPersistentVar("$wood_bag", "", API.PersistentVar.Char)
        if not bag:
            API.SysMsg("Target a container for your logs.")
            bag = API.RequestTarget(30)
            if not bag: return

            API.SavePersistentVar("$wood_bag", str(bag), API.PersistentVar.Char)
        Serials.move_destination = int(bag)
        
    HarvestAroundYou()
    API.HeadMsg("Complete", API.Player, 33)


# Execute Main
Main()