from f5.models.F5.backend.Certificate import Certificate as Backend


class Certificate:
    def __init__(self, assetId: int, partitionName: str, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assetId = int(assetId)
        self.partitionName = partitionName
        self.name = name



    ####################################################################################################################
    # Public methods
    ####################################################################################################################

    def delete(self):
        try:
            Backend.delete(self.assetId, self.partitionName, self.name, "cert")
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def list(assetId) -> dict:
        try:
            return Backend.list(assetId, "cert")
        except Exception as e:
            raise e



    @staticmethod
    def install(assetId: int, data: dict) -> None:
        try:
            Backend.install(assetId, "cert", data)
        except Exception as e:
            raise e
