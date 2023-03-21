from typing import List, Dict, Union

from f5.models.F5.Asset.repository.Asset import Asset as Repository
from f5.models.F5.Asset.repository.AssetAssetDr import AssetAssetDr as AssetDrRepository

from f5.helpers.Misc import Misc
from f5.helpers.Log import Log


class Asset:
    def __init__(self, assetId: int, includeDr: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id: int = int(assetId)
        self.address: str = ""
        self.fqdn: str = ""
        self.baseurl: str = ""
        self.tlsverify: bool = True
        self.datacenter: str = ""
        self.environment: str = ""
        self.position: str = ""

        self.username: str = ""
        self.password: str = ""

        self.assetsDr: List[Dict[str, Union[Asset, bool]]] = []

        self.__load(includeDr=includeDr)



    ####################################################################################################################
    # Public methods
    ####################################################################################################################

    def repr(self):
        return Misc.deepRepr(self)



    def modify(self, data: dict) -> None:
        try:
            Repository.modify(self.id, data)

            for k, v in Misc.toDict(data).items():
                setattr(self, k, v)
        except Exception as e:
            raise e



    def delete(self) -> None:
        try:
            Repository.delete(self.id)
            del self
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public methods - disaster recovery relation
    ####################################################################################################################

    def drDataList(self, onlyEnabled: bool = True) -> list:
        try:
            return AssetDrRepository.list(primaryAssetId=int(self.id), onlyEnabled=onlyEnabled)
        except Exception as e:
            raise e



    def drModify(self, drAssetId: int, enabled: bool) -> None:
        try:
            AssetDrRepository.modify(primaryAssetId=self.id, drAssetId=int(drAssetId), enabled=enabled)
        except Exception as e:
            raise e



    def drRemove(self, drAssetId: int) -> None:
        try:
            AssetDrRepository.delete(primaryAssetId=self.id, drAssetId=int(drAssetId))
        except Exception as e:
            raise e



    def drAdd(self, drAssetId: int, enabled: bool) -> None:
        try:
            AssetDrRepository.add(primaryAssetId=self.id, drAssetId=int(drAssetId), enabled=enabled) # circular path forbidden.
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def dataList(includeDr: bool = True) -> list:
        try:
            l = Repository.list()
            if includeDr:
                for asset in l:
                    asset["assetsDr"] = list()

                    for dr in AssetDrRepository.list(primaryAssetId=asset["id"]):
                        asset["assetsDr"].append({
                            "asset": dr,
                            "enabled": dr["enabled"]
                        })
        except Exception as e:
            raise e

        return l



    @staticmethod
    def add(data: dict) -> None:
        from f5.models.Permission.Partition import Partition as PermissionPartition

        try:
            aId = Repository.add(data)

            # When inserting an asset, add the "any" partition (Permission).
            PermissionPartition.add(aId, "any")
        except Exception as e:
            raise e



    @staticmethod
    def purgeAll() -> None:
        from f5.models.Permission.Partition import Partition

        try:
            Partition.purgeAll()
            Repository.purgeAll()
        except Exception as e:
            raise e



    ####################################################################################################################
    # Private methods
    ####################################################################################################################

    def __load(self, includeDr: bool = True) -> None:
        try:
            data = Repository.get(self.id)
            for k, v in data.items():
                setattr(self, k, v)

            if includeDr:
                # Load related disaster recovery assets.
                for dr in AssetDrRepository.list(primaryAssetId=self.id):
                    self.assetsDr.append({
                        "asset": Asset(dr["id"]),
                        "enabled": dr["enabled"]
                    })
        except Exception as e:
            raise e
