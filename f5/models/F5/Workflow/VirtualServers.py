from collections import OrderedDict

from f5.models.F5.Node import Node
from f5.models.F5.Monitor import Monitor
from f5.models.F5.Pool import Pool
from f5.models.F5.Certificate import Certificate
from f5.models.F5.Key import Key
from f5.models.F5.SnatPool import SnatPool
from f5.models.F5.Profile import Profile
from f5.models.F5.Irule import Irule
from f5.models.F5.VirtualServer import VirtualServer
from f5.models.History.History import History

from f5.helpers.Log import Log
from f5.helpers.Exception import CustomException


class VirtualServersWorkflow:
    def __init__(self, assetId: int, partitionName: str, data: dict, user: dict):
        self.assetId = assetId
        self.partitionName = partitionName
        self.data = data
        self.username = user["username"]
        self.routeDomain = ""

        if "routeDomainId" in data["virtualServer"] and data["virtualServer"]["routeDomainId"]:
            self.routeDomain = "%"+str(data["virtualServer"]["routeDomainId"]) # for example: %1.

        self.__createdObjects = {
            "node": [],
            "monitor": {},
            "pool": {},
            "poolMember": [],
            "irule": [],
            "profile": [],
            "snatPool": {},
            "key": [],
            "certificate": [],
            "virtualServer": {}
        }

        self.__usedObjects = {
            "node": []
        }



    ####################################################################################################################
    # Public methods
    ####################################################################################################################

    def add(self) -> None:
        try:
            #vsType = self.data["virtualServer"]["type"]

            self.__createNodes()
            self.__createMonitor()
            self.__createPool()
            self.__createPoolMembers()
            self.__createSnatPool()
            self.__createIrules()
            self.__createProfiles()
            self.__createVirtualServer()

            self.__logCreatedObjects()
        except KeyError:
            self.__cleanCreatedObjects()
            raise CustomException(status=400, payload={"F5": "Wrong input."})
        except Exception as e:
            raise e



    ####################################################################################################################
    # Public static methods
    ####################################################################################################################

    @staticmethod
    def relatedF5Objects() -> list:
        return ["node", "monitor", "pool", "poolMember", "snatPool", "irule", "profile", "certificate", "key", "virtualServer"]



    ####################################################################################################################
    # Private methods
    ####################################################################################################################

    def __createNodes(self) -> None:
        j = 0

        for el in self.data["pool"]["nodes"]:
            nodeName = el["name"]
            nodeAddress = el["address"]

            if nodeName == nodeAddress:
                self.data["pool"]["nodes"][j]["name"] = nodeName = "node_"+nodeName # this fixes an F5 issue (name = address when using a root domain different than the default).

            try:
                Log.actionLog("Virtual server workflow: attempting to create node: "+str(nodeAddress))

                Node.add(self.assetId, {
                    "name": nodeName,
                    "address": nodeAddress+self.routeDomain,
                    "partition": self.partitionName,
                    "State": "up"
                })

                # Keep track of CREATED nodes.
                self.__createdObjects["node"].append({
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": nodeName,
                    "address": nodeAddress+self.routeDomain,
                })
            except Exception as e:
                if e.__class__.__name__ == "CustomException":
                    if "F5" in e.payload and e.status == 409 and "already exists" in e.payload["F5"]:
                        Log.log("Node "+str(nodeName)+"/"+str(nodeAddress)+" already exists with the same address/name; using it. ")

                        # Keep track of USED node.
                        self.__usedObjects["node"].append({
                            "asset": self.assetId,
                            "partition": self.partitionName,
                            "name": nodeName,
                            "address": nodeAddress+self.routeDomain,
                        })
                    else:
                        self.__cleanCreatedObjects()
                        raise e
                else:
                    self.__cleanCreatedObjects()
                    raise e

            j += 1

        Log.actionLog("Created objects: "+str(self.__createdObjects))
        Log.actionLog("Reused existent objects: "+str(self.__usedObjects))



    def __createMonitor(self) -> None:
        if "monitor" in self.data:
            monitorName = self.data["monitor"]["name"]
            monitorType = self.data["monitor"]["type"]

            try:
                Log.actionLog("Virtual server workflow: attempting to create monitor: "+str(monitorName))

                mData = {
                    "name": monitorName,
                    "partition": self.partitionName
                }

                if "send" in self.data["monitor"]:
                    mData["send"] = self.data["monitor"]["send"]
                if "recv" in self.data["monitor"]:
                    mData["recv"] = self.data["monitor"]["recv"]

                Monitor.add(self.assetId, monitorType, mData)

                # Keep track of CREATED monitor.
                self.__createdObjects["monitor"] = {
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": monitorName,
                    "type": monitorType
                }
            except Exception as e:
                self.__cleanCreatedObjects()
                raise e

            Log.actionLog("Created objects: "+str(self.__createdObjects))



    def __createPool(self) -> None:
        poolName = self.data["pool"]["name"]

        try:
            Log.actionLog("Virtual server workflow: attempting to create pool: "+str(poolName))

            Pool.add(self.assetId, {
                "name": poolName,
                "partition": self.partitionName,
                "monitor": "/"+self.partitionName+"/"+self.data["monitor"]["name"],
                "loadBalancingMode": self.data["pool"]["loadBalancingMode"]
            })

            # Keep track of CREATED pool.
            self.__createdObjects["pool"] = {
                "asset": self.assetId,
                "partition": self.partitionName,
                "name": poolName
            }
        except Exception as e:
            self.__cleanCreatedObjects()
            raise e

        Log.actionLog("Created objects: "+str(self.__createdObjects))



    def __createPoolMembers(self) -> None:
        poolName = self.data["pool"]["name"]

        if "nodes" in self.data["pool"]:
            for el in self.data["pool"]["nodes"]:
                nodeName = el["name"]
                poolMemberPort = el["port"]
                poolMemberName = nodeName+":"+str(poolMemberPort)

                try:
                    Log.actionLog("Virtual server workflow: attempting to create pool members: associate "+str(nodeName)+" to "+str(poolName)+" on port "+str(poolMemberPort))

                    Pool(self.assetId, self.partitionName, poolName).addMember({
                            "name": "/"+self.partitionName+"/"+poolMemberName,
                            "State": "up",
                            "session": "user-enabled"
                        }
                    )

                    # Keep track of CREATED pool members.
                    self.__createdObjects["poolMember"].append({
                        "asset": self.assetId,
                        "partition": self.partitionName,
                        "pool": poolName,
                        "name": poolMemberName
                    })
                except Exception as e:
                    self.__cleanCreatedObjects()
                    raise e

            Log.actionLog("Created objects: "+str(self.__createdObjects))



    def __createIrules(self) -> None:
        if "irules" in self.data:
            for el in self.data["irules"]:
                iruleName = el["name"]
                iruleCode = ""
                if "code" in el:
                    iruleCode = el["code"]

                try:
                    Log.actionLog("Virtual server workflow: attempting to create irule: "+str(iruleName))

                    Irule.add(self.assetId, {
                        "name": iruleName,
                        "partition": self.partitionName,
                        "apiAnonymous": iruleCode
                    })

                    # Keep track of CREATED irule.
                    self.__createdObjects["irule"].append({
                        "asset": self.assetId,
                        "partition": self.partitionName,
                        "name": iruleName
                    })
                except Exception as e:
                    self.__cleanCreatedObjects()
                    raise e

            Log.actionLog("Created objects: "+str(self.__createdObjects))



    def __createCertificateOrKey(self, o: str, name: str, text: str) -> None:
        if o in ("certificate", "key"):
            try:
                Log.actionLog("Virtual server workflow: attempting to create "+o+": "+str(name))

                if o == "certificate":
                    Certificate.install(self.assetId, self.partitionName, {
                        "name": name,
                        "content_base64": text
                    })
                else:
                    Key.install(self.assetId, self.partitionName, {
                        "name": name,
                        "content_base64": text
                    })

                # Keep track of CREATED object.
                self.__createdObjects[o].append({
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": name
                })
            except Exception as e:
                self.__cleanCreatedObjects()
                raise e

            Log.actionLog("Created objects: "+str(self.__createdObjects))
        else:
            raise NotImplementedError



    def __createProfiles(self) -> None:
        for el in self.data["profiles"]:
            profileName = el["name"]
            profileType = el["type"]

            data = {
                "name": profileName,
                "partition": self.partitionName
            }

            # Additional POST data.
            if "idleTimeout" in el:
                data["idleTimeout"] = el["idleTimeout"]
            if "defaultsFrom" in el:
                data["defaultsFrom"] = el["defaultsFrom"]

            try:
                # Create key and certificate.
                certName = keyName = chainName = self.data["virtualServer"]["name"]

                if "cert" in el and el["cert"]:
                    if "certName" in el \
                            and el["certName"]:
                        certName = el["certName"]

                    self.__createCertificateOrKey("certificate", name=certName, text=el["cert"])
                    data["cert"] = "/"+self.partitionName+"/"+certName # use the created one.

                if "key" in el and el["key"]:
                    if "keyName" in el \
                            and el["keyName"]:
                        keyName = el["keyName"]

                    self.__createCertificateOrKey("key", name=keyName, text=el["key"])
                    data["key"] = "/"+self.partitionName+"/"+keyName

                if "chain" in el and el["chain"]:
                    if "chainName" in el \
                            and el["chainName"]:
                        chainName = el["chainName"]

                    self.__createCertificateOrKey("certificate", name=chainName, text=el["chain"])
                    data["chain"] = "/"+self.partitionName+"/"+chainName

                # Create profile.
                Log.actionLog("Virtual server workflow: attempting to create profile: "+str(profileName))

                Profile.add(self.assetId, profileType, data)

                # Keep track of CREATED profile.
                self.__createdObjects["profile"].append({
                    "asset": self.assetId,
                    "partition": self.partitionName,
                    "name": profileName,
                    "type": profileType
                })
            except Exception as e:
                self.__cleanCreatedObjects()
                raise e

        Log.actionLog("Created objects: "+str(self.__createdObjects))



    def __createSnatPool(self) -> None:
        if self.data["virtualServer"]["snat"] == "snat":
            if "snatPool" in self.data:
                snatPoolName = self.data["snatPool"]["name"]
                snatPoolMembers = list()

                try:
                    Log.actionLog("Virtual server workflow: attempting to create SNAT pool: "+str(snatPoolName))

                    if "members" in self.data["snatPool"]:
                        for m in self.data["snatPool"]["members"]:
                            snatPoolMembers.append("/"+self.partitionName+"/"+m+self.routeDomain)

                    SnatPool.add(self.assetId, {
                        "name": snatPoolName,
                        "partition": self.partitionName,
                        "members": snatPoolMembers
                    })

                    # Keep track of CREATED snatPool.
                    self.__createdObjects["snatPool"] = {
                        "asset": self.assetId,
                        "partition": self.partitionName,
                        "name": snatPoolName
                    }
                except Exception as e:
                    self.__cleanCreatedObjects()
                    raise e

            Log.actionLog("Created objects: "+str(self.__createdObjects))
        else:
            Log.actionLog("Snat pool creation skipped.")



    def __createVirtualServer(self) -> None:
        snatpoolName = ""
        profiles = list()
        irules = list()

        virtualServerName = self.data["virtualServer"]["name"]
        virtualServerDestination = self.data["virtualServer"]["destination"]
        virtualServerMask = self.data["virtualServer"]["mask"]
        virtualServerSource = self.data["virtualServer"]["source"]

        try:
            Log.actionLog("Virtual server workflow: attempting to create virtual server: "+str(virtualServerName))

            if "snatPool" in self.data \
                    and "name" in self.data["snatPool"]:
                snatpoolName = self.data["snatPool"]["name"]

            virtualServerSnat = {
                "type": self.data["virtualServer"]["snat"],
                "pool": snatpoolName
            }

            if self.routeDomain:
                i, m = virtualServerSource.split("/")
                virtualServerSource = i + self.routeDomain + "/" + m

                i, p = virtualServerDestination.split(":")
                virtualServerDestination = i + self.routeDomain + ":" + p

            if "profiles" in self.data:
                for el in self.data["profiles"]:
                    context = "all"
                    if "context" in el:
                        context = el["context"]

                    profiles.append({
                        "name": "/"+self.partitionName+"/"+el["name"],
                        "context": context
                    })

            if "irules" in self.data:
                for el in self.data["irules"]:
                    irules.append("/"+self.partitionName+"/"+el["name"])

            VirtualServer.add(self.assetId, {
                "name": virtualServerName,
                "partition": self.partitionName,
                "destination": "/"+self.partitionName+"/"+virtualServerDestination,
                "ipProtocol": "tcp",
                "rules": irules,
                "profiles": profiles,
                "mask": virtualServerMask,
                "pool":  "/"+self.partitionName+"/"+self.data["pool"]["name"],
                "source": virtualServerSource,
                "sourceAddressTranslation": virtualServerSnat
            })

            # Keep track of CREATED virtual server.
            self.__createdObjects["virtualServer"] = {
                "asset": self.assetId,
                "partition": self.partitionName,
                "name": virtualServerName
            }
        except Exception as e:
            self.__cleanCreatedObjects()
            raise e

        Log.actionLog("Created objects: "+str(self.__createdObjects))


    
    def __cleanCreatedObjects(self):
        Log.log("Virtual server workflow: cleanup")

        # Reverse elements in order to delete from leaf to branch.
        self.__createdObjects = OrderedDict(
            reversed(list(
                self.__createdObjects.items())
            )
        )

        for k, v in self.__createdObjects.items():
            if k == "virtualServer":
                if "name" in v:
                    virtualServerName = v["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup virtualServer "+virtualServerName)

                        vs = VirtualServer(self.assetId, self.partitionName, virtualServerName)
                        vs.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+virtualServerName)

            if k == "irule":
                for n in v:
                    iruleName = n["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup irule "+iruleName)

                        irule = Irule(self.assetId, self.partitionName, iruleName)
                        irule.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+iruleName)

            if k == "profile":
                for n in v:
                    profileName = n["name"]
                    profileType = n["type"]
                    try:
                        Log.log("Virtual server workflow: cleanup profile "+profileName)

                        profile = Profile(self.assetId, self.partitionName, profileType, profileName)
                        profile.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+profileName)

            if k == "certificate":
                for n in v:
                    certificateName = n["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup certificate "+certificateName)

                        certificate = Certificate(self.assetId, self.partitionName, certificateName)
                        certificate.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+certificateName)

            if k == "key":
                for n in v:
                    keyName = n["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup certificate "+keyName)

                        key = Key(self.assetId, self.partitionName, keyName)
                        key.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+keyName)

            if k == "poolMember":
                for n in v:
                    poolMemberName = n["name"]
                    poolName = n["pool"]
                    try:
                        Log.log("Virtual server workflow: cleanup pool member "+poolMemberName)

                        poolMember = Pool(self.assetId, poolName, self.partitionName).member(poolMemberName)
                        poolMember.delete()
                    except Exception:
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+poolMemberName)

            if k == "pool":
                if "name" in v:
                    poolName = v["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup pool "+poolName)

                        pool = Pool(self.assetId, self.partitionName, poolName)
                        pool.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+poolName)

            if k == "snatPool":
                if "name" in v:
                    snatPoolName = v["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup snatpool "+snatPoolName)

                        snatpool = SnatPool(self.assetId, self.partitionName, snatPoolName)
                        snatpool.delete()
                    except Exception:
                        # If deletion failed, log.
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+snatPoolName)

            if k == "monitor":
                if "name" in v:
                    monitorName = v["name"]
                    monitorType = v["type"]
                    try:
                        Log.log("Virtual server workflow: cleanup monitor "+monitorName)

                        monitor = Monitor(self.assetId, self.partitionName, monitorType, monitorName)
                        monitor.delete()
                    except Exception:
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+monitorName)

            if k == "node":
                for n in v:
                    nodeName = n["name"]
                    try:
                        Log.log("Virtual server workflow: cleanup node "+nodeName)

                        node = Node(self.assetId, self.partitionName, nodeName)
                        node.delete()
                    except Exception:
                        Log.actionLog("[ERROR] Virtual server workflow: failed to clean "+nodeName)



    def __logCreatedObjects(self) -> None:
        for k, v in self.__createdObjects.items():
            try:
                if k in ("virtualServer", "pool", "monitor", "snatPool"):
                    if "name" in v:
                        History.add({
                            "username": self.username,
                            "action": "[WORKFLOW] "+self.data["virtualServer"]["name"]+" creation ("+self.data["virtualServer"]["type"]+", SNAT:"+self.data["virtualServer"]["snat"]+")",
                            "asset_id": self.assetId,
                            "config_object_type": k,
                            "config_object": "/"+self.partitionName+"/"+v["name"],
                            "status": "created"
                            })

                if k in ("node", "poolMember", "irule", "profile", "key", "certificate"):
                    for n in v:
                        History.add({
                            "username": self.username,
                            "action": "[WORKFLOW] "+self.data["virtualServer"]["name"]+" creation ("+self.data["virtualServer"]["type"]+", SNAT:"+self.data["virtualServer"]["snat"]+")",
                            "asset_id": self.assetId,
                            "config_object_type": k,
                            "config_object": "/"+self.partitionName+"/"+n["name"],
                            "status": "created"
                        })
            except Exception:
                pass
