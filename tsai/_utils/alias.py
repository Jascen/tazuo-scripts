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