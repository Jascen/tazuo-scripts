"""
Name: YAO - Yet Another Organizer
Description: Used to move items that pass the configured Filter Criteria from a Source container to a Destination container.
Author: Tsai (Ultima: Memento)
GitHub Source: Jascen/tazuo-scripts
Version: v1.0 (Legion)
"""

#import API

import System
from tsai._services.filter.useroptions import UserOptions


from tsai._services.filter.systemcontainers import SystemContainers


def GetIgnoredFilters():
    """
    User-Defined list of Filters that should not be organized.
    """

    return [
        # Filter Criteria for items to ignore
    ]


def GetOrganizers():
    """
    User-constructed list of Organizers to execute.

    Organizer(<Source>, <Destination>, <Filters>)
    - Source - Serial. The container to open and run the provided item Filters against
    - Destination - Serial. The container that an item is moved to if it passes at least one Filter
    - Filters - Array of Filters. All items found in the Source container are run through each Filter individually

    Warning: The order of your Organizers matters. Organizers are executed from first to last (top-down order).
    An item will be moved to the Destination first Organizer whose Filter passed

    Shorthand notation:
    - You may use number (0xab3) (0x123abc) values to check against an item's Grapich/ID or Serial
    - You may use string ("this is a string") values to check against item's `Name` or `Property values`
    - String notation may also use the `&` operator to require multiple conditions
      - Example: All unidentified wands
        - Filter = "wand & unidentified"
        - Item must contain "wand" in the `Name` or `Property values`
        - Item must contain "unidentified" in the `Name` or `Property values`

    Combining filters:
    - As use-cases evolve, you may need to invert filters to exclude items
    - Example: All non-weapon artifacts
        - Filter = All("Artifact", Not("Weapon"))
            - Item must contain "artifact" in the `Name` or `Property values`
            - Item must NOT contain "weapon" in either the `Name` or the `Property values`

    Explicit notation:
    - As use-cases evolve, you may need to explicitly create Filters yourself
        - Example: All non-weapon artifacts
          - Filter = AllFilter(["Artifact", NotFilter("Weapon")])
    """

    source = SystemContainers.PromptForSource

    return [
        # Example Organizer
        Organizer(source, [
            # Destination Container Serials
        ], [
            # Filter Criteria
        ]),
    ]

#-----------------------------------------------------------
# Warning - You should not be editing after this line
#-----------------------------------------------------------
#-----------------------------------------------------------
# Warning - You should not be editing after this line
#-----------------------------------------------------------
#-----------------------------------------------------------
# Warning - You should not be editing after this line
#-----------------------------------------------------------


#---------------------------------------
# System Configuration
#---------------------------------------
from tsai._services.filter.systemconfig import SystemConfig


#---------------------------------------
# Filter Abstractions - Do not touch
#---------------------------------------
from tsai._services.filter.core import *


def Not(filter):
    return NotFilter(filter)


def All(*filters):
    filter_list = []
    for filter in filters:
        filter_list.append(filter)
    return AllFilter(filter_list)


def Any(*filters):
    filter_list = []
    for filter in filters:
        filter_list.append(filter)
    return AnyFilter(filter_list)


#---------------------------------------
# Filters
#---------------------------------------
from tsai._services.filter.implementations import *


#---------------------------------------
# Filter Utilities
#---------------------------------------
from tsai._services.filter.utilities import *


#------------------------
# Lists of Items
#------------------------
from tsai._services.filter.fixedlists import FixedLists


#------------------------
# Organizer
#------------------------
class Organizer:
    def __init__(self, source, destination, filters):
        self.source = source
        self.destination = destination
        self.filters = filters

    def Test(self, item):
        for filter in self.filters:
            if filter.Test(item):
                return True
        return False


#------------------------
# Item Utilities
#------------------------
class ItemUtils:
    @classmethod
    def GetItemsRecursive(cls, source_container, items, process_item_predicate, include_children=True):
        container_items = API.ItemsInContainer(source_container, False)

        for item in container_items:
            if not process_item_predicate(item):
                continue

            if include_children and cls.HasProperty(item, "contents:"):
                container = cls.OpenContainer(item.Serial)
                if container == None:
                    continue

                cls.GetItemsRecursive(item.Serial, items, process_item_predicate, include_children)
            else:
                items.append(item)

    @classmethod
    def HasProperty(cls, item, substring):
        name_and_props = API.ItemNameAndProps(item.Serial, False)
        if not name_and_props:
            return False

        properties = name_and_props.lower().split('\n')[1:]
        for property in properties:
            if substring in property:
                return True
        return False

    @classmethod
    def OpenContainer(cls, serial):
        item = API.FindItem(serial)
        if item == None:
            API.SysMsg("Failed to find container ({})".format(hex(serial)))
            return None

        # TODO: Can we check to make sure a container's contents are loaded?
        API.UseObject(item.Serial)
        API.Pause(1.0)

        return item.Serial

    @classmethod
    def HasCapacity(cls, serial, reserved_space=5):
        item = API.FindItem(serial)
        if item == None:
            return False

        name_and_props = API.ItemNameAndProps(serial, False)
        if not name_and_props:
            return True  # Assume it has capacity if we can't check

        props = name_and_props.split('\n')[1:]

        # Look for "Contents: X/Y items"
        for line in props:
            if line.strip().startswith("Contents"):
                # Parse "Contents: 123/125 items" format
                try:
                    parts = line.split(':')[1].strip().split('/')
                    current = int(parts[0].strip())
                    max_items = int(parts[1].split()[0].strip())
                    return current < (max_items - reserved_space)
                except:
                    return True

        return True


#------------------------
# Movement
#------------------------
class Runner:
    @classmethod
    def MoveTo(cls, serial, max_attempts=50):
        mob = API.FindMobile(serial)
        item = API.FindItem(serial)
        target = mob if mob else item

        if not target:
            return False

        i = 0
        while target.Distance > 2 and i < max_attempts:
            # Use pathfinding instead of manual run
            API.PathfindEntity(serial, 2, False, 1)
            while API.Pathfinding():
                API.Pause(0.25)

            i += 1

        return target.Distance <= 2


#------------------------
# Runner
#------------------------
class OrganizerRunner:
    def __init__(self):
        self.prompt_serial = None

    def Validate(self, organizers):
        for organizer in organizers:
            if not self.__getDestination(organizer.destination):
                API.SysMsg("Failed to open Destination ({}).".format(organizer.destination))

    def Process(self, organizers, ignored_filter):
        # Aggregate by Source and Destination
        organizers_by_source = self.__groupBySource(organizers)
        for source in organizers_by_source:
            source_serial = self.__resolveSource(source)

            source_container = ItemUtils.OpenContainer(source_serial)
            if not source_container:
                API.SysMsg("Failed to open Source ({}).".format(source))
                return

            # Get all the items
            items = []
            ItemUtils.GetItemsRecursive(source_container, items, lambda item: ignored_filter == None or not ignored_filter.Test(item), UserOptions.Open_Child_Containers)
            total_items = len(items)

            # Process the list of items
            for i, item in enumerate(items):
                API.SysMsg("Processing item ({} of {}).".format(i + 1, total_items))
                if ignored_filter != None and ignored_filter.Test(item):
                    continue

                for organizer in organizers_by_source[source]:
                    if organizer.Test(item):
                        # Find the first container with capacity
                        destination = self.__getDestination(organizer.destination)
                        if destination == None:
                            API.SysMsg("Skipping organizer. Failed to find Destination with capacity ({}).".format(organizer.destination))
                            continue

                        if UserOptions.Move_To_Destination:
                            if not self.__moveToDestination(destination):
                                API.SysMsg("Failed to move to Destination ({}).".format(hex(destination) if isinstance(destination, System.UInt32) else destination))

                        if UserOptions.Output_Item_Move_Messages:
                            API.SysMsg("Moved ({}) to ({})".format(item.Name, hex(destination)))

                        API.MoveItem(item.Serial, destination)
                        API.Pause(1.0)
                        break

    def __resolveSource(self, source):
        if source == SystemContainers.PromptForSource:
            if not self.prompt_serial:
                API.SysMsg("Target the source container", 32)
                self.prompt_serial = API.RequestTarget()
            return self.prompt_serial
        elif source == SystemContainers.PlayerBackpack:
            return API.Backpack
        elif source == SystemContainers.PlayerBank:
            return API.Bank
        else:
            return source

    def __getDestination(self, destinations):
        if not isinstance(destinations, list):
            destinations = [destinations]

        for destination in destinations:
            if destination is None:
                continue

            dest_serial = self.__resolveDestination(destination)
            if dest_serial and ItemUtils.HasCapacity(dest_serial):
                return dest_serial

        return None

    def __resolveDestination(self, destination):
        if destination == SystemContainers.PlayerBackpack:
            return API.Backpack
        elif destination == SystemContainers.PlayerBank:
            return API.Bank
        else:
            return destination

    def __groupBySource(self, organizers):
        organizers_by_source = {}
        for organizer in organizers:
            if organizer.destination == None:
                continue

            if not organizer.source in organizers_by_source:
                organizers_by_source[organizer.source] = []

            organizers_by_source[organizer.source].append(organizer)

        return organizers_by_source

    def __moveToDestination(self, destination_serial):
        # Special handling for bank
        if destination_serial == API.Bank:
            vault_type_id = 0x436
            vault = API.FindType(vault_type_id)
            if not vault:
                API.SysMsg("Failed to find Vault.")
                return False

            if not Runner.MoveTo(vault.Serial):
                API.SysMsg("Failed to move to Vault.")
                return False

            API.UseObject(vault.Serial)
            API.Pause(1.0)

        elif destination_serial != API.Backpack:
            # Move to the destination container
            if not Runner.MoveTo(destination_serial):
                return False

        return True


#------------------------
# Main
#------------------------
def Main():
    ignored_filter = None
    ignored_filters = GetIgnoredFilters()
    if 0 < len(ignored_filters):
        FilterUtils.ResolveFilters(ignored_filters, SystemConfig.AndOperatorCharacter)
        ignored_filter = AnyFilter(ignored_filters)

    organizers = GetOrganizers()

    for organizer in organizers:
        # Convert any shorthand
        FilterUtils.ResolveFilters(organizer.filters, SystemConfig.AndOperatorCharacter)
        if SystemConfig.LogFilterSummary:
            print(list(map(str, organizer.filters)))

    runner = OrganizerRunner()
    runner.Process(organizers, ignored_filter)

    API.HeadMsg("Execution Completed", API.Player.Serial)


# Execute Main
Main()
