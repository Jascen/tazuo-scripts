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


    @classmethod
    def remove(cls, alias, scope):
        API.RemovePersistentVar(alias, scope)