# import API


class PlayerUtils:
    @staticmethod
    def ClearHands():
        if API.FindLayer("TwoHanded"):
            API.Pause(1)
            API.ClearLeftHand()
        if API.FindLayer("OneHanded"):
            API.Pause(1)
            API.ClearLeftHand()


    @staticmethod
    def HasCapacity(weight_required):
        available = API.Player.WeightMax - API.Player.Weight

        return weight_required <= available