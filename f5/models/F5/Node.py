from dataclasses import dataclass

from f5.models.F5.backend.Node import Node as Backend


class Node:
    def __init__(self, assetId: int, partitionName: str, nodeName: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @dataclass
        class Fqdn:
            addressFamily: str
            autopopulate: str
            interval: str
            downInterval: int

        self.assetId = int(assetId)
        self.partition = partitionName
        self.name = nodeName

        self.fullPath: str
        self.generation: int
        self.selfLink: str
        self.address: str
        self.connectionLimit: int
        self.dynamicRatio: int
        self.ephemeral: str
        self.fqdn: Fqdn
        self.logging: str
        self.monitor: str
        self.rateLimit: str
        self.ratio: int
        self.session: str
        self.state: str



    ####################################################################################################################
    # Public methods
    ####################################################################################################################

    def modify(self, data):
        try:
            Backend.modify(self.assetId, self.partition, self.name, data)
        except Exception as e:
            raise e



    def delete(self):
        try:
            Backend.delete(self.assetId, self.partition, self.name)
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def list(assetId: int, partitionName: str, silent: bool = False) -> dict:
        try:
            return Backend.list(assetId, partitionName, silent)
        except Exception as e:
            raise e



    @staticmethod
    def add(assetId: int, data: dict) -> None:
        try:
            Backend.add(assetId, data)
        except Exception as e:
            raise e



    @staticmethod
    def getNameFromAddress(assetId: int, partitionName: str, address: str, silent: bool = False) -> str:
        name = ""
        try:
            data = Node.list(assetId, partitionName, silent=silent)
            for nel in data["items"]:
                if nel["address"] == address:
                    name = nel["name"]

            return name
        except Exception as e:
            raise e
