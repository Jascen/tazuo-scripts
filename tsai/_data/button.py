class _ButtonDefs:
    def __init__(self, normal, pressed=None, hover=None):
        self.normal = normal
        self.pressed = pressed if pressed else normal
        self.hover = hover if hover else normal

class ButtonDefs:
    Default = _ButtonDefs(2444, 2443)
    Blank = _ButtonDefs(5547)