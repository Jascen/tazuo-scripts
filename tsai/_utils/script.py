# import API

from tsai._utils.logger import Logger


class ScriptUtils:
    def check_auto_pause():
        while API.Player.IsDead or API.Player.InWarMode:
            if API.Player.InWarMode:
                Logger.log("Script is paused due to war mode")
            API.Pause(1)