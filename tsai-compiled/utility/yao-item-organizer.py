"""
Name: YAO - Yet Another Organizer
Description: Used to move items that pass the configured Filter Criteria from a Source container to a Destination container.
Author: Tsai (Ultima: Memento)
GitHub Source: Jascen/tazuo-scripts
Version: v1.0 (Legion)
"""

#import API
import System

class UserOptions:
    Open_Child_Containers = True  # If you want to open the child containers when searching Source containers
    Move_To_Destination = True  # If you want your character to move within 2 tiles of the Destination containers
    Output_Item_Move_Messages = True  # If you want to see what item is moved and the destination that it is moved to


class SystemContainers:
    """
    Special aliases used by the system. These may be referenced by the User.
    """
    PromptForSource = "$Prompt"
    PlayerBackpack = "backpack"
    PlayerBank = "bank"  # When used as a Destination, the script will search for a Vault and open it


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
class SystemConfig:
    LogFilterSummary = False
    AndOperatorCharacter = "&"


#---------------------------------------
# Filter Abstractions - Do not touch
#---------------------------------------
class MultiFilterBase:
    def __init__(self, filters):
        self.filters = filters


    def __str__(self):
        return ", ".join(map(str, self.filters))


class MetaFilterBase:
    def __init__(self, filter):
        self.filter = filter


    def __str__(self):
        return str(self.filter)


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
class NameFilter:
    """
    - A case-insensitive partial string match against an item's `Name`
        - `name` - The string to search for
        - `hue` - Optional. If provided, the item must have this hue to pass the Filter
        - `partial_match` - Optional. If `False`, the item name must exactly match the provided value
    """
    def __init__(self, name, hue=-1, partial_match=True):
        self.name = name
        self.name_normalized = name.lower()
        self.hue = hue
        self.partial_match = partial_match


    @classmethod
    def PartialSearch(cls, item, name_normalized):
        return name_normalized in item.Name.lower()


    def Test(self, item):
        if self.hue != -1 and self.hue != item.Hue:
            return False
        if self.partial_match:
            return self.PartialSearch(item, self.name_normalized)
        return item.Name.lower() == self.name_normalized


    def __str__(self):
        name = "Partial Name" if self.partial_match else "Name"
        return "{} ({})".format(name, self.name_normalized)


class MaxPropertyCountFilter:
    """
    - A count of the number of properties
        - `max_count` - The maximum number of properties an item can have
    """
    def __init__(self, max_count):
        self.max_count = max_count


    def Test(self, item):
        # In Legion, we need to get the item properties and count them
        name_and_props = API.ItemNameAndProps(item.Serial, False)
        if not name_and_props:
            return True  # If we can't get props, allow it
        lines = name_and_props.split('\n')
        return len(lines) - 1 <= self.max_count # Remove one for Name


    def __str__(self):
        return "Max Props ({})".format(self.max_count)


class PropertyFilter:
    """
    - A case-insensitive partial string match against an item's `Properties`
        - `property` - The string value to search for
        - `hue` - Optional. If provided, the item must have this hue to pass the Filter
        - `partial_match` - Optional. If `False`, the item property must exactly match the provided value
    """
    def __init__(self, property, hue=-1, partial_match=True):
        self.property = property
        self.property_normalized = property.lower()
        self.hue = hue
        self.partial_match = partial_match


    def Test(self, item):
        if self.hue != -1 and self.hue != item.Hue:
            return False

        return self.__hasProperty(item, self.property_normalized, self.partial_match)


    def __hasProperty(self, item, value, partial_match):
        name_and_props = API.ItemNameAndProps(item.Serial, False)
        if not name_and_props:
            return False

        props = name_and_props.lower().split('\n')
        for property in props[1:]: # Skip the Name line
            if partial_match:
                if value in property: return True
            else:
                if value == property: return True
        return False


    def __str__(self):
        name = "Partial Prop" if self.partial_match else "Prop"
        return "{} ({})".format(name, self.property_normalized)


class PropertyValueFilter:
    """
    - Exact match against a specific property
        - `property` - The exact name of the property
        - `value` - The numeric or string value to search for
    """
    def __init__(self, property, value, case_insensitive=True):
        if case_insensitive:
            value = value.lower()

        self.property = property
        self.value = value
        self.is_numeric = not isinstance(value, str)


    def Test(self, item):
        # In Legion, we need to check item attributes directly
        if hasattr(item, self.property):
            property_value = getattr(item, self.property)
            if self.is_numeric:
                property_value = int(property_value)
            return property_value == self.value
        return False


    def __str__(self):
        name = "#" if self.is_numeric else "Str"
        return "{} Prop Val ({})".format(name, self.property)


class SerialFilter:
    """
    - Exact match against an item's `Serial`
        - `serial` - The ID to search for
    """
    def __init__(self, serial):
        self.serial = serial


    def Test(self, item):
        return item.Serial == self.serial


    def __str__(self):
        return "Serial ({})".format(self.serial)


class TypeFilter:
    """
    - Exact match against an item `Graphic` or `ID`
        - `type_id` - The item must have this Graphic or ID
        - `hue` - Optional. If provided, the item must have this hue to pass the Filter
    """
    def __init__(self, type_id, hue=-1):
        self.type_id = type_id
        self.hue = hue


    def Test(self, item):
        return (self.hue == -1 or self.hue == item.Hue) and item.Graphic == self.type_id


    def __str__(self):
        return "Type ({})".format(hex(self.type_id))


class TypeRangeFilter:
    """
    - Requires an item `Graphic` or `ID` to be >= starting ID and <= ending ID
        - `type_start` - The starting graphic ID
        - `type_end` - The ending graphic ID
    """
    def __init__(self, type_start, type_end):
        self.type_start = type_start
        self.type_end = type_end


    def Test(self, item):
        return self.type_start <= item.Graphic and item.Graphic <= self.type_end


    def __str__(self):
        return "Type Range ({} to {})".format(hex(self.type_start), hex(self.type_end))


class NotFilter(MetaFilterBase):
    """
    - Inverts the response of the provided Filter
        - `filter` - A single Filter to check
    """
    def __init__(self, filter):
        MetaFilterBase.__init__(self, filter)


    def Test(self, item):
        return not self.filter.Test(item)


    def __str__(self):
        return "Not: {}".format(self.filter)


class AllFilter(MultiFilterBase):  # AND
    """
    - All provided Filters must pass in order for the item to be moved
        - `filters` - An array of Filters to check
    """
    def __init__(self, filters):
        MultiFilterBase.__init__(self, filters)


    def Test(self, item):
        for filter in self.filters:
            if not filter.Test(item):
                return False
        return True


class AnyFilter(MultiFilterBase):  # OR
    """
    - At least one Filter must pass in order for the item to be moved
        - `filters` - A list of Filters to check
    """
    def __init__(self, filters):
        MultiFilterBase.__init__(self, filters)


    def Test(self, item):
        for filter in self.filters:
            if filter.Test(item):
                return True
        return False


#---------------------------------------
# Filter Utilities
#---------------------------------------
class FilterUtils:
    @classmethod
    def ConvertShorthand(cls, value, and_operator):
        if not isinstance(value, str) and not isinstance(value, int):
            return value  # Assume it's a filter
        if and_operator == None or isinstance(value, int):
            return cls.__CreateImplicitFilter(value)

        return cls.__ConvertOperators(value, and_operator)


    @classmethod
    def ResolveFilters(cls, filters, and_operator=None):
        for i, filter in enumerate(filters):
            if isinstance(filter, MultiFilterBase):
                cls.ResolveFilters(filter.filters, and_operator)
            elif isinstance(filter, MetaFilterBase):
                temp = [filter.filter]
                cls.ResolveFilters(temp, and_operator)
                filter.filter = temp[0]
            else:
                filters[i] = cls.ConvertShorthand(filter, and_operator)


    @classmethod
    def __ConvertOperators(cls, value, and_operator):
        start_index = -1
        and_list = []
        for i, c in enumerate(value):
            if c != and_operator:
                continue

            # Double operator, restart
            if i == start_index + 1:
                start_index = i
                continue

            # Extract value
            current_value = value[start_index + 1 : i].strip()
            if current_value:
                and_list.append(current_value)

            start_index = i

        # Flush final index
        if start_index:
            last_value = value[start_index + 1 :: ].strip()
            if last_value:
                and_list.append(last_value)

        if not and_list:
            return None

        return AllFilter(list(map(cls.__CreateImplicitFilter, and_list)))


    @classmethod
    def __CreateImplicitFilter(cls, value):
        if isinstance(value, int):
            return AnyFilter([SerialFilter(value), TypeFilter(value)])
        if isinstance(value, str):
            return AnyFilter([NameFilter(value), PropertyFilter(value)])
        return None


#------------------------
# Lists of Items
#------------------------
class FixedLists:
    Instruments = AnyFilter([
        TypeFilter(0xe9d),  # Tambourine
        TypeFilter(0xe9e),  # Tambourine w/ Tassel
        TypeFilter(0xeb3),  # Lute
        TypeFilter(0xeb2),  # Harp
        TypeFilter(0xe9c),  # Drum
        TypeFilter(0x2805),  # Flute
    ])
    Slayers = AnyFilter([
        PropertyFilter("Giant Killer"),
        PropertyFilter("Supernatural Vanquishing"),
        PropertyFilter("Weed Ruin"),
        PropertyFilter("Serpentaur Execution"),
        PropertyFilter("Orcish Demise"),
        PropertyFilter("Ogre Extinction"),
        PropertyFilter("Golem Destruction"),
    ])
    Jewelry = AnyFilter([
        NameFilter("earring"),
        NameFilter("beads"),
        NameFilter("amulet"),
        NameFilter("necklace"),
        NameFilter("bracelet"),
        AllFilter([  # Rings - The coloring of names provides False positives because "ring" is a substring of "string"
            AnyFilter([
                NameFilter(" ring"),
                NameFilter("ring "),
            ]),
            NotFilter(PropertyFilter("requirement"))
        ]),
    ])


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
