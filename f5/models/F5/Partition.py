from f5.models.F5.backend.Partition import Partition as Backend


class Partition:
    def __init__(self, assetId: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assetId = int(assetId)



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def list(assetId: int) -> dict:
        try:
            return Backend.list(assetId)
        except Exception as e:
            raise e
