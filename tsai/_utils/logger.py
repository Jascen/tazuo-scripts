# import API

from tsai._utils.hue import Hue

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