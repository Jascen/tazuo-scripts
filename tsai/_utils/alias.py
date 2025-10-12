# import API


class AliasUtils:
    @classmethod
    def GetValue(cls, alias, scope):
        """Gets the value for the `alias`"""
        value = API.GetPersistentVar(alias, "", scope)

        return value if value else None


    @classmethod
    def GetValueOrDefault(cls, alias, scope, default):
        """Gets the value or the default"""
        return API.GetPersistentVar(alias, default, scope)


    @classmethod
    def GetValueOrPrompt(cls, alias, scope, prompt_message, timeout=30):
        """Gets the Serial for the `alias` or prompts if it is not found"""
        value = cls.GetValue(alias, scope)

        return value if value else cls.Prompt(alias, scope, prompt_message, timeout)


    @classmethod
    def Prompt(cls, alias, scope, prompt_message, timeout=30):
        """Prompts the user to set a value for the alias"""
        serial = cls.GetValue(alias, scope)
        if not serial:
            API.SysMsg(prompt_message)
            serial = API.RequestTarget(timeout)
            if not serial: return None

            API.SavePersistentVar(alias, str(serial), scope)

        return serial