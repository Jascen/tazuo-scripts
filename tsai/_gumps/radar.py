# import API

from nesci._Utils.Gump import Gump
from nesci._Utils.Color import Color

from tsai._utils.logger import Logger


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
        g.addButton("Detect", g.width - 80, initial_y - 18, "default", self.detect_nodes)
        
        initial_y += 20
        # TODO: Border for buttons
        player = API.Player
        for x in range(0 - self.radius, self.radius + 1):
            for y in range(0 - self.radius, self.radius + 1):
                radar_button = RadarButton(player.X + x, player.Y + y, x, y, self.button_size)
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
                button.click_fn = None
                button.set_visible(False)
                button.exact_x = API.Player.X + x
                button.exact_y = API.Player.Y + y
                i += 1

        self.detect_fn()


    def sync_position(self, x, y):
        # Logger.Trace("[Radar.sync_position]")
        for radar_button in self.radar_buttons:
            radar_button.check_match(x, y)


class RadarButton:
    def __init__(self, exact_x, exact_y, rel_x, rel_y, button_size):
        button = API.CreateSimpleButton("", button_size, button_size)
        button.IsVisible = False
        button.Alpha = 1
        button.SetBackgroundHue(1)
        self.button = button
        self.active = False
        self.exact_x = exact_x
        self.exact_y = exact_y
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.click_fn = None
        self.node_hue = None


    def button_clicked(self):
        Logger.debug("[RadarButton.button_clicked]")
        if self.click_fn:
            self.click_fn()
    

    def set_visible(self, visible):
        Logger.trace("[RadarButton.set_visible]")
        if self.button.IsVisible == visible:
            return

        self.button.IsVisible = visible


    def set_location(self, x, y):
        Logger.trace("[RadarButton.set_location]")
        self.exact_x == x
        self.exact_y == y


    def set_node_hue(self, hue):
        Logger.trace("[RadarButton.set_node_hue]")
        self.node_hue = hue
        if self.button.Hue != hue:
            self.button.Hue = hue


    def check_match(self, x, y):
        # Logger.Trace("[RadarButton.check_match]")
        if self.exact_x == x and self.exact_y == y:
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