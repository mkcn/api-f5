from f5.models.F5.Node import Node
from f5.models.F5.Monitor import Monitor
from f5.models.F5.Irule import Irule
from f5.models.F5.Pool import Pool
from f5.models.F5.SnatPool import SnatPool
from f5.models.F5.Profile import Profile
from f5.models.F5.VirtualServer import VirtualServer
from f5.models.History import History

from f5.helpers.Log import Log


class VirtualServerWorkflow:
    def __init__(self, assetId: int, partitionName: str, virtualServerName: str, user: dict):
        try:
            self.profiles = list()
            self.irules = list()
            self.policies = list()
            self.monitor = {
                "name": "",
                "type": ""
            }
            self.poolName = ""
            self.snatPool = ""
            self.nodes = list()

            self.__deletedObjects = {
                "node": [],
                "monitor": {},
                "pool": {},
                "poolMember": [],
                "profile": [],
                "irule": [],
                "snatPool": {},
                "virtualServer": {}
            }

            self.assetId = assetId
            self.partitionName = partitionName
            self.virtualServerName = virtualServerName
            self.username = user["username"]

            self.__info()
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public methods
    ####################################################################################################################

    def delete(self) -> None:
        self.__deleteVirtualServer()
        self.__deleteIrules()
        self.__deleteSnatPool()
        self.__deleteProfiles()
        self.__deletePool()
        self.__deleteMonitor()
        self.__deleteNodes()

        self.__logDeletedObjects()



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def relatedF5Objects() -> list:
        return ["node", "monitor", "pool", "poolMember", "snatPool", "irule", "profile", "virtualServer"]



    ####################################################################################################################
    # Private methods
    ####################################################################################################################

    def __info(self) -> None:
        try:
            vs = VirtualServer(self.assetId, self.partitionName, self.virtualServerName)

            # General info.
            info = vs.info()
            try:
                self.poolName = info["pool"].split("/")[2]

                if "sourceAddressTranslation" in info \
                        and "pool" in info["sourceAddressTranslation"]:
                    self.snatPool = info["sourceAddressTranslation"]["pool"]

                for ir in info["rules"]:
                    self.irules.append({"name": ir})
            except Exception:
                pass

            # Related profiles.
            profiles = vs.profiles()["items"]
            for profile in profiles:
                self.profiles.append({
                    "name": profile["name"],
                    "type": VirtualServerWorkflow.__getProfileType(self.assetId, self.partitionName, profile["name"])
                })

            # Related policies.
            #policies = vs.policies()["items"]
            #for policy in policies:
            #    self.policies.append(policy["name"])

            if self.poolName:
                # Pool info -> monitor.
                pool = Pool(self.assetId, self.partitionName, self.poolName)
                poolInfo = pool.info()
                if "monitor" in poolInfo:
                    self.monitor["name"] = poolInfo["monitor"].split("/")[2]
                    self.monitor["type"] = VirtualServerWorkflow.__getMonitorType(self.assetId, self.partitionName, self.monitor["name"])

                # Pool members of self.poolName -> nodes.
                poolMembers = Pool(self.assetId, self.partitionName, self.poolName).members()
                for pm in poolMembers:
                    self.nodes.append({
                        "name": Node.getNameFromAddress(
                            self.assetId,
                            self.partitionName,
                            pm["address"],
                            silent=True
                        ),
                        "address": pm["address"]
                    })
        except Exception as e:
            raise e


    def __deleteVirtualServer(self) -> None:
        try:
            Log.actionLog("Virtual server deletion workflow: attempting to delete virtual server: "+str(self.virtualServerName))

            vs = VirtualServer(self.assetId, self.partitionName, self.virtualServerName)
            vs.delete()

            self.__deletedObjects["virtualServer"] = {
                "asset": self.assetId,
                "partition": self.partitionName,
                "name": self.virtualServerName
            }

        except Exception as e:
            if e.__class__.__name__ == "CustomException":
                if "F5" in e.payload and e.status == 400 and "in use" in e.payload["F5"]:
                    Log.log("Virtual server "+str(self.virtualServerName)+" in use; not deleting it. ")
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete virtual server "+self.virtualServerName+": "+str(e.payload))
            else:
                Log.log("[ERROR] Virtual server deletion workflow: cannot delete virtual server "+self.virtualServerName+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __deleteIrules(self) -> None:
        Log.actionLog("Virtual server deletion workflow: attempting to delete irules: "+str(self.irules))

        for el in self.irules:
            iruleName = el["name"].split("/")[2]
            try:
                irule = Irule(self.assetId, self.partitionName, iruleName)
                irule.delete()

                self.__deletedObjects["irule"].append({
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": iruleName
                })

            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 400 and "in use" in e.payload["F5"]:
                        Log.log("Irule "+str(iruleName)+" in use; not deleting it. ")
                    else:
                        Log.log("[ERROR] Virtual server deletion workflow: cannot delete irule "+iruleName+": "+str(e.payload))
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete irule "+iruleName+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __deleteProfiles(self) -> None:
        Log.actionLog("Virtual server deletion workflow: attempting to delete profiles: "+str(self.profiles))

        for p in self.profiles:
            profileName = p["name"]
            profileType = p["type"]

            try:
                profile = Profile(self.assetId, self.partitionName, profileType, profileName)
                profile.delete()

                self.__deletedObjects["profile"].append({
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": profileName,
                    "type": profileType
                })

            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 400 and "in use" in e.payload["F5"]:
                        Log.log("Profile "+str(profileName)+" in use; not deleting it. ")
                    else:
                        Log.log("[ERROR] Virtual server deletion workflow: cannot delete profile "+profileName+": "+str(e.payload))
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete profile "+profileName+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __deleteMonitor(self) -> None:
        if self.monitor["name"]:
            try:
                Log.actionLog("Virtual server deletion workflow: attempting to delete monitor: "+str(self.monitor["name"]))

                monitor = Monitor(self.assetId, self.partitionName, self.monitor["type"], self.monitor["name"])
                monitor.delete()

                self.__deletedObjects["monitor"] = {
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": self.monitor["name"],
                    "type": self.monitor["type"]
                }

            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 400 and "in use" in e.payload["F5"]:
                        Log.log("Monitor "+str(self.monitor["name"])+" in use; not deleting it. ")
                    else:
                        Log.log("[ERROR] Virtual server deletion workflow: cannot delete monitor "+self.monitor["name"]+": "+str(e.payload))
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete monitor "+self.monitor["name"]+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __deletePool(self) -> None:
        if self.poolName:
            try:
                Log.actionLog("Virtual server deletion workflow: attempting to delete pool: "+str(self.poolName))

                pool = Pool(self.assetId, self.partitionName, self.poolName)
                pool.delete()

                self.__deletedObjects["pool"] = {
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": self.poolName
                }

            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 400 and "in use" in e.payload["F5"]:
                        Log.log("Pool "+str(self.poolName)+" in use; not deleting it. ")
                    else:
                        Log.log("[ERROR] Virtual server deletion workflow: cannot delete pool "+self.poolName+": "+str(e.payload))
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete pool "+self.poolName+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __deleteSnatPool(self) -> None:
        if self.snatPool:
            try:
                Log.actionLog("Virtual server deletion workflow: attempting to delete snat pool: "+str(self.snatPool))

                snatpool = SnatPool(self.assetId, self.partitionName, self.snatPool.split("/")[2])
                snatpool.delete()

                self.__deletedObjects["snatPool"] = {
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": self.poolName
                }

            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 400 and "in use" in e.payload["F5"]:
                        Log.log("Snat pool "+str(self.snatPool)+" in use; not deleting it. ")
                    else:
                        Log.log("[ERROR] Virtual server deletion workflow: cannot delete snat pool "+self.snatPool+": "+str(e.payload))
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete snat pool "+self.snatPool+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __deleteNodes(self) -> None:
        Log.actionLog("Virtual server deletion workflow: attempting to delete nodes: "+str(self.nodes))

        for n in self.nodes:
            nodeName = n["name"]
            nodeAddress = n["address"]

            try:
                node = Node(self.assetId, self.partitionName, nodeName)
                node.delete()

                self.__deletedObjects["node"].append({
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": nodeName,
                    "address": nodeAddress
                })

            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 400 and "is referenced" in e.payload["F5"]:
                        Log.log("Node "+str(nodeName)+" in use; not deleting it. ")
                    else:
                        Log.log("[ERROR] Virtual server deletion workflow: cannot delete node "+nodeName+": "+str(e.payload))
                else:
                    Log.log("[ERROR] Virtual server deletion workflow: cannot delete node "+nodeName+": "+e.__str__())

        Log.actionLog("Deleted objects: "+str(self.__deletedObjects))



    def __logDeletedObjects(self) -> None:
        for k, v in self.__deletedObjects.items():
            try:
                if k in ("virtualServer", "pool", "monitor", "snatPool"):
                    if "name" in v:
                        History.add({
                            "username": self.username,
                            "action": "[WORKFLOW] "+self.virtualServerName+" deletion",
                            "asset_id": self.assetId,
                            "config_object_type": k,
                            "config_object": "/"+self.partitionName+"/"+v["name"],
                            "status": "deleted"
                            })

                if k in ("node", "profile", "irule"):
                    for n in v:
                        History.add({
                            "username": self.username,
                            "action": "[WORKFLOW] "+self.virtualServerName+" deletion",
                            "asset_id": self.assetId,
                            "config_object_type": k,
                            "config_object": "/"+self.partitionName+"/"+n["name"],
                            "status": "deleted"
                        })
            except Exception:
                pass



    ####################################################################################################################
    # Private static methods
    ####################################################################################################################

    @staticmethod
    def __getProfileType(assetId, partitionName, profileName):
        # Profile type.
        # The only way to get a profile type is to iterate through all the possible profile types.
        # A not so small pain in the ass.

        # Try avoiding the iterations method by testing the most used profiles, first.
        for pt in ["fastl4", "tcp", "http", "client-ssl"]:
            try:
                p = Profile(assetId, partitionName, pt, profileName)
                p.info(silent=True) # probe.

                return pt # if found valid profile.
            except Exception:
                pass

        profileTypes = Profile.types(assetId, partitionName)
        for pt in profileTypes:
            try:
                p = Profile(assetId, partitionName, pt, profileName)
                p.info(silent=True)

                return pt
            except Exception:
                pass



    @staticmethod
    def __getMonitorType(assetId, partitionName, monitorName):
        for mtype in ["tcp-half-open", "http"]:
            try:
                monitor = Monitor(assetId, partitionName, mtype, monitorName)
                monitor.info(silent=True) # probe.

                return mtype # if found valid monitor.
            except Exception:
                pass

        monitorTypes = Monitor.types(assetId, partitionName)
        for mtype in monitorTypes:
            try:
                monitor = Monitor(assetId, partitionName, mtype, monitorName)
                monitor.info(silent=True)

                return mtype
            except Exception:
                pass
