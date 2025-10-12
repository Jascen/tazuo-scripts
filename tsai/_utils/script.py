# import API

from tsai._utils.logger import Logger


class ScriptUtils:
    def CheckAutoPause():
        while API.Player.IsDead or API.Player.InWarMode:
            if API.Player.InWarMode:
                Logger.Log("Script is paused due to war mode")
            API.Pause(1)