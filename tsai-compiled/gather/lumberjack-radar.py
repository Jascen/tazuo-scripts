"""
Name: Lumerjack Radar Assistant
Description: Detects trees within 6 tiles and hues them
  - Clicking the `Detect` button or `Q` hotkey will re-hue nearby trees and add them to the Radar
  - Clicking the button on the Radar will pathfind to and harvest the node
  - `E` hotkey will harvest the closest unharvested node
- Other notable features
  - Automatically finds and equips hatchet from your backpack
  - Move Logs/Bark Fragments to a container (usually placed on a pack animal) when overweight
  - Can also stop execution by using War Mode
Author: Tsai (Ultima: Memento)
Version: v1.0
"""


from decimal import Decimal
import time
# import API

# import API

class _ButtonDefs:
    def __init__(self, normal, pressed=None, hover=None):
        self.normal = normal
        self.pressed = pressed if pressed else normal
        self.hover = hover if hover else normal

class ButtonDefs:
    Default = _ButtonDefs(2444, 2443)
    Blank = _ButtonDefs(5547)
class Color:
    defaultRed = "#b80028"
    defaultGreen = "#00b828"
    defaultLightGray = "#b8b8c0"
    defaultGray = "#585858"
    defaultBlack = "#000000"
    defaultWhite = "#f8f8f8"
    defaultBorder = "#a87000"
# import API




class Gump:
    def __init__(self, width, height, onCloseCb=None, withStatus=True):
        self.width = width
        self.height = height
        self.onCloseCb = onCloseCb
        self.withStatus = withStatus

        self.gump = API.CreateGump(True, True)
        self.subGumps = []
        self.bg = None
        self._running = True
        self.buttons = []
        self.skillTextBoxes = []
        self.pendingCallbacks = []
        self.tabGumps = {}

        self.gump.SetWidth(self.width)
        self.gump.SetHeight(self.height)
        self.gump.CenterXInViewPort()
        self.gump.CenterYInViewPort()
        self.borders = self._setBorders(0, 0, self.width, self.height)
        self._setBackground()

        if withStatus:
            self.statusLabel = API.CreateGumpLabel("Ready.")
            self.statusLabel.SetX(10)
            self.statusLabel.SetY(self.height - 30)
            self.gump.Add(self.statusLabel)

        self._lastCheckTime = time.time()
        self._checkInterval = 0.1

    def create(self):
        API.AddGump(self.gump)

    def tick(self):
        if not self._running or self.gump.IsDisposed:
            self._running = False
            if self.onCloseCb:
                self.onCloseCb()
            else:
                self.destroy()
                API.Stop()
            return

        now = time.time()
        if (now - self._lastCheckTime) >= self._checkInterval:
            self.checkValidateForm()
            self._checkEvents()
            self._lastCheckTime = now

    def tickSubGumps(self):
        for subGump, position, _ in self.subGumps:
            if subGump._running and not subGump.gump.IsDisposed:
                self._setSubGumpPosition(subGump.gump, subGump.width, subGump.height, position)

    def destroy(self):
        if not self._running:
            return
        self._running = False
        for tab in self.tabGumps.values():
            try:
                if not tab.IsDisposed:
                    tab.Dispose()
            except:
                pass
        for subGump in self.subGumps:
            subGump.destroy()
        try:
            if not self.gump.IsDisposed:
                self.gump.Dispose()
        except Exception as e:
            API.SysMsg(f"Gump.Dispose failed: {e}", 33)
        API.SysMsg("Gump destroyed.", 66)

    def createSubGump(self, width, height, position="bottom", withStatus=False, alwaysVisible=True):
        gump = Gump(width, height, withStatus=withStatus)
        self._setSubGumpPosition(gump.gump, width, height, position)
        API.AddGump(gump.gump)
        self.subGumps.append((gump, position, alwaysVisible))
        return gump

    def setStatus(self, text, hue=996):
        if self.withStatus:
            self.statusLabel.Text = text
            if hue:
                self.statusLabel.Hue = hue

    def onClick(self, cb, startText=None, endText=None):
        def wrapped():
            if startText:
                self.setStatus(startText)
            cb()
            if endText:
                self.setStatus(endText)

        return wrapped

    def setActiveTab(self, name):
        if name not in self.tabGumps:
            return
        for subGumps, _, alwaysVisible in self.subGumps:
            if not alwaysVisible:
                subGumps.gump.IsVisible = False
        tabGump = self.tabGumps[name]
        tabGump.gump.IsVisible = True

    def addTabButton(self, name, iconType, gumpWidth, callback=None, yOffset=45, withStatus=False, label="", isDarkMode=False):
        y = 10 + len(self.tabGumps) * yOffset
        x = 0

        def onClick():
            self.setActiveTab(name)
            if callback:
                callback()

        btn = self.addButton(label, x + 5, y, iconType, self.onClick(onClick), isDarkMode)
        self.buttons.append(btn)
        tabGump = self.createSubGump(gumpWidth, self.height, "right", withStatus, False)
        tabGump.gump.IsVisible = False
        self.tabGumps[name] = tabGump
        return tabGump

    def addColorBox(self, x, y, height, width, colorHex=Color.defaultBlack, opacity=1):
        colorBox = API.CreateGumpColorBox(opacity, colorHex)
        colorBox.SetX(x)
        colorBox.SetY(y)
        colorBox.SetWidth(width)
        colorBox.SetHeight(height)
        self.gump.Add(colorBox)
        return colorBox        

    def addCheckbox(self, label, x, y, isChecked, callback, hue=996):
        checkbox = API.CreateGumpCheckbox(
            label, hue, isChecked
        )
        checkbox.SetX(x)
        checkbox.SetY(y)
        if callback:
            API.AddControlOnClick(checkbox, callback)
        self.gump.Add(checkbox)
        return checkbox

    def addButton(self, label, x, y, button_def, callback, isDarkMode = False):
        btn = API.CreateGumpButton(
            "", 996, button_def.normal, button_def.pressed, button_def.hover
        )
        btn.SetX(x)
        btn.SetY(y)
        API.AddControlOnClick(btn, callback)
        self.gump.Add(btn)
        if button_def == ButtonDefs.Default:
            color = Color.defaultBlack
            if isDarkMode:
                color = Color.defaultWhite
            labelObj = self.addTtfLabel(label, x, y, 63, 23, 12, color, "center", callback)
        else:
            labelObj = API.CreateGumpLabel(label)
            labelObj.SetY(y)
            labelObj.SetX(x)
        API.AddControlOnClick(labelObj, callback)
        self.gump.Add(labelObj)
        return btn

    def addTtfLabel(
        self, label, x, y, width, height, fontSize, fontColorHex, position, callback
    ):
        ttfLabel = API.CreateGumpTTFLabel(
            label, fontSize, fontColorHex, maxWidth=width, aligned=position
        )
        centerY = y + int(height / 2) - 6
        ttfLabel.SetX(x)
        ttfLabel.SetY(centerY)
        # API.AddControlOnClick(ttfLabel, self.onClick(callback))
        self.gump.Add(ttfLabel)
        return ttfLabel

    def addLabel(self, text, x, y, hue=None):
        label = API.CreateGumpLabel(text)
        label.SetX(x)
        label.SetY(y)
        if hue:
            label.Hue = hue
        self.gump.Add(label)
        return label

    def addSkillTextBox(
        self, defaultValue, x, y, minValue=0, maxValue=120, width=60, height=24
    ):
        clampedValue = max(minValue, min(maxValue, Decimal(defaultValue)))
        borderColor = "".join(Color.defaultWhite)
        borders = []
        for bx, by, bw, bh in [
            (x - 2, y - 2, width + 4, 2),
            (x - 2, y + height, width + 4, 2),
            (x - 2, y, 2, height),
            (x + width, y, 2, height),
        ]:
            border = API.CreateGumpColorBox(1, borderColor)
            border.SetX(bx)
            border.SetY(by)
            border.SetWidth(bw)
            border.SetHeight(bh)
            self.gump.Add(border)
            borders.append(border)
        textbox = API.CreateGumpTextBox(str(clampedValue), width, height, False)
        textbox.SetX(x)
        textbox.SetY(y)
        self.gump.Add(textbox)
        self.skillTextBoxes.append((textbox, minValue, maxValue, borders))
        return textbox

    def checkValidateForm(self):
        for skillTextBox, minValue, maxValue, borders in self.skillTextBoxes:
            isValidated = self._getValidatedNumber(skillTextBox, minValue, maxValue)
            color = Color.defaultWhite if isValidated else Color.defaultRed
            hue = Color.convertFromHexToHue(color)
            for border in borders:
                border.Hue = hue
            if not isValidated:
                return False
        return True

    def _getValidatedNumber(self, textbox, minValue, maxValue):
        try:
            if not textbox.Text:
                return False
            val = Decimal(textbox.Text)
            return minValue <= val <= maxValue
        except ValueError:
            return False

    def _checkEvents(self):
        API.ProcessCallbacks()
        while self.pendingCallbacks:
            cb = self.pendingCallbacks.pop(0)
            cb()

    def _setBackground(self):
        if not self.bg:
            self.bg = API.CreateGumpColorBox(0.75, Color.defaultBlack)
            self.gump.Add(self.bg)
        self.bg.SetWidth(self.width - 10)
        self.bg.SetHeight(self.height - 10)
        self.bg.SetX(0)
        self.bg.SetY(0)

    def _setBorders(
        self,
        x,
        y,
        width,
        height,
        frameColor=Color.defaultBorder,
        thickness=5,
        inside=False,
    ):
        positions = (
            [
                (x, y, width, thickness),
                (x, y + height - thickness, width, thickness),
                (x, y, thickness, height),
                (x + width - thickness, y, thickness, height),
            ]
            if inside
            else [
                (-thickness, -thickness, width, thickness),
                (-thickness, height - thickness * 2, width, thickness),
                (-thickness, -thickness, thickness, height),
                (width - thickness * 2, -thickness, thickness, height),
            ]
        )
        borders = []
        for bx, by, bw, bh in positions:
            border = API.CreateGumpColorBox(1, frameColor)
            border.SetX(bx)
            border.SetY(by)
            border.SetWidth(bw)
            border.SetHeight(bh)
            self.gump.Add(border)
            borders.append(border)
        return borders

    def _setSubGumpPosition(self, gump, width, height, position):
        gx, gy = self.gump.GetX(), self.gump.GetY()
        if position == "bottom":
            gump.SetX(gx)
            gump.SetY(gy + self.height)
        elif position == "top":
            gump.SetX(gx)
            gump.SetY(gy - height)
        elif position == "center":
            gump.SetX(gx + self.width // 2 - width // 2)
            gump.SetY(gy + self.height // 2 - height // 2)
        elif position == "left":
            gump.SetX(gx - width)
            gump.SetY(gy)
        elif position == "right":
            gump.SetX(gx + self.width)
            gump.SetY(gy)
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


class Radar:
    def __init__(self, detect_fn):
        self.radius = 6 # Distance from player to check
        self.button_size = 14
        self.button_padding = int(0.75 * self.button_size)
        self.button_length = self.button_size + self.button_padding
        self.detect_fn = detect_fn
        self.gump = None
        self.radar_buttons = []


    def create_gump(self, label):
        Logger.debug("[Radar.create_gump]")
        number_of_buttons = 1 + (2 * self.radius)
        width = number_of_buttons * (self.button_size + self.button_padding)
        height = width + 50
        g = Gump(width, height, None, False)
        g.gump.CanCloseWithRightClick = False
        initial_y = 20
        g.addTtfLabel(label, 5, 0, width, initial_y, 20, Color.defaultWhite, "left", None)
        g.addButton("Detect", g.width - 80, initial_y - 18, ButtonDefs.Default, self.detect_nodes)
        
        initial_y += 20
        # TODO: Border for buttons
        player = API.Player
        for x in range(0 - self.radius, self.radius + 1):
            for y in range(0 - self.radius, self.radius + 1):
                radar_button = RadarButton(x, y, self.button_size)
                radar_button.button.SetX((self.radius + x) * self.button_length)
                radar_button.button.SetY(initial_y + (self.radius + y) * self.button_length)

                API.AddControlOnClick(radar_button.button, radar_button.button_clicked) # Add click handler

                self.radar_buttons.append(radar_button)
                g.gump.Add(radar_button.button) # Add to gump

        g.create()
        self.gump = g


    def detect_nodes(self):
        Logger.debug("[Radar.detect_nodes]")

        # Hide everything
        i = 0
        for x in range(0 - self.radius, self.radius + 1):
            for y in range(0 - self.radius, self.radius + 1):
                button = self.radar_buttons[i]
                button.entity = FakeEntity(API.Player.X + x, API.Player.Y + y)
                button.click_fn = None
                button.set_visible(False)
                i += 1

        self.detect_fn()


    def sync_position(self, x, y):
        # Logger.Trace("[Radar.sync_position]")
        for radar_button in self.radar_buttons:
            radar_button.check_match(x, y)


class RadarButton:
    def __init__(self, rel_x, rel_y, button_size):
        button = API.CreateSimpleButton("", button_size, button_size)
        button.IsVisible = False
        button.Alpha = 1
        button.SetBackgroundHue(1)
        self.button = button
        self.active = False
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.entity = None 
        self.click_fn = None
        self.node_hue = None


    def button_clicked(self):
        Logger.debug("[RadarButton.button_clicked]")
        if self.click_fn:
            self.click_fn()


    def check_match(self, x, y):
        # Logger.Trace("[RadarButton.check_match]")
        if not self.entity:
            return

        if self.entity.X == x and self.entity.Y == y:
            if not self.active:
                Logger.trace("Setting button to active")
                self.active = True
                self.button.Hue = 32 # Red
        elif self.active:
            self.active = False
            if not self.node_hue:
                Logger.trace("Deactivating button")
                self.set_visible(False)
                return

            Logger.trace("Re-coloring button")
            self.button.Hue = self.node_hue
        else:
            return

        if self.button.Hue and not self.button.IsVisible:
            self.set_visible(True)


    def set_entity(self, entity):
        Logger.trace("[RadarButton.set_entity]")
        self.entity = entity


    def set_node_hue(self, hue):
        Logger.trace("[RadarButton.set_node_hue]")
        self.node_hue = hue
        if self.button.Hue != hue:
            self.button.Hue = hue


    def set_visible(self, visible):
        Logger.trace("[RadarButton.set_visible]")
        if self.button.IsVisible == visible:
            return

        self.button.IsVisible = visible


class FakeEntity:
    def __init__(self, x, y):
        self.X = x
        self.Y = y
        self.Distance = 10000
class GeneralItem:
    """Basic details for a single type of item"""
    def __init__(self, graphic, name, hue = -1):
        self.graphic = graphic
        self.name = name
        self.hue = hue
# import API

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


# Resources
Board          = GeneralItem(7127, "board")
Ingot          = GeneralItem(7154, "ingot")
Leather        = GeneralItem(4225, "leather")
Log            = GeneralItem(7136, "log")
BarkFragment   = GeneralItem(12687, "bark fragment")

# Tools
Hatchet        = GeneralItem(3907, "hatchet")


class LumberjackService:
    _types_to_move = [
        Log.graphic,
        BarkFragment.graphic
    ]
    _stump_graphic = 0x0E59


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
        Logger.debug("[LumberjackService.get_nearby_trees]")
        trees = []
        statics = API.GetStaticsInArea(API.Player.X - radius, API.Player.Y - radius, API.Player.X + radius, API.Player.Y + radius)
        
        for static in statics:
            if (static.IsTree or (not ignore_stumps and static.Graphic == cls._stump_graphic)) \
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
        Logger.trace("[LumberjackAssistant.hide_statics]")
        for static in API.GetStaticsAt(tree.X, tree.Y):
            static.SetHue(hue)
            static.Graphic = graphic if graphic != None else cls._stump_graphic


    @classmethod
    def move_gathered(cls, destination, clear_hands_before_move):
        Logger.debug("[LumberjackService.move_gathered]")

        for type_id in cls._types_to_move:
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


LumberjackSparkle = GeneralItem(14138, "a rich tree")


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
            radar_buttons = self.radar_buttons[:]
            radar_buttons.sort(key=lambda tree: tree.entity.Distance if tree.entity and tree.entity.Distance and tree.entity else 10000) # Large number

            for radar_button in radar_buttons:
                if radar_button.button.Hue == UserOptions.Tree_To_Harvest_Hue:
                    if radar_button.click_fn:
                        radar_button.click_fn()
                    return
        except Exception as e:
            Logger.error(str(repr(e)))


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
            Logger.debug("Overweight. Moving items!")
            LumberjackService.move_gathered(self.move_destination, UserOptions.Clear_hands_before_move)
        else:
            Logger.error("Overweight. Moving items!")
            API.Stop()


    def _get_nearby_trees(self):
        Logger.debug("[LumberjackRadar._get_nearby_trees]")
        for static in LumberjackService.filter_nearby_trees(self.radius, self.ignored_tree_graphics, UserOptions.Tree_To_Harvest_Hue, UserOptions.Harvested_Tree_Hue, self._mark_tree_processed, False):
            self._mark_tree_processed(static)


    def _harvest(self, tree, radar_button):
        Logger.debug("[LumberjackRadar._harvest]")
        self.overweight_check()
        if not LumberjackService.ensure_hatchet():
            return

        API.TrackingArrow(tree.X, tree.Y)
        if LumberjackService.harvest(tree):
            LumberjackService.hide_statics(tree, UserOptions.Harvested_Tree_Hue)
            radar_button.set_node_hue(UserOptions.Harvested_Tree_Hue)
            API.TrackingArrow(-1, -1)


    def _mark_tree_processed(self, static):
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


class OverweightBehavior:
    Stop = 0 # Stop the script
    Move = 1 # Move the boards/logs to a bag or pack animal


# Manual Configuration - Begin
# Logger.DEBUG = True
# Logger.TRACE = True
class UserOptions:
    Overweight_threshold = 60 # When your available weight is less than this value, execute Overweight behavior
    Overweight_behavior = OverweightBehavior.Move
    # Max_retries = 3 # Default to 15
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


main()
