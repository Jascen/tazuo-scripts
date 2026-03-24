"""
Name: Memento+TazUO quick Autolooter

** USER CONFIGURABLE OPTIONS ARE AT THE TOP **

Description:
  - Prompts for a target for TazUO's Autoloot function
  - Optionally calls and auto-targets the container using Memento's [Autoloot command
Author: Tsai (Ultima: Memento)
GitHub Source: Jascen/tazuo-scripts
Version: v0.1
"""

class UserOptions:
    Hotkey = None
    Memento_Autoloot_Timeout_Seconds = 2 # Set to 0 for no [autoloot command

def do_autoloot():
    API.HeadMsg("Target container to autoloot", API.Player, 33)
    targ = API.RequestTarget()
    if not targ:
        return

    if 0 < UserOptions.MEMENTO_AUTOLOOT_TIMEOUT_SECONDS:
        API.Msg("[autoloot")
        if not API.WaitForTarget("neutral", UserOptions.MEMENTO_AUTOLOOT_TIMEOUT_SECONDS):
            API.HeadMsg("Timed out waiting for Memento autoloot target!", API.Player, 33)
        else:
            API.Target(targ)
            API.Pause(0.5)

    API.AutoLootContainer(targ)

if not UserOptions.Hotkey:
    do_autoloot()
else:
    API.HeadMsg(f"Autoloot running. Press '{UserOptions.Hotkey}' to prompt", API.Player, 33)
    API.OnHotKey(UserOptions.Hotkey, do_autoloot)
    while not API.StopRequested:
        API.ProcessCallbacks()
        API.Pause(0.25)