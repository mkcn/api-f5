#import asyncio
#from asgiref.sync import sync_to_async
import threading

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from f5.models.F5.Profile import Profile
from f5.models.Permission.Permission import Permission

from f5.serializers.F5.Profiles import F5ProfilesSerializer as ProfilesSerializer
from f5.serializers.F5.Profile import F5ProfileSerializer as ProfileSerializer

from f5.controllers.CustomController import CustomController

from f5.helpers.Lock import Lock
from f5.helpers.Conditional import Conditional
from f5.helpers.Log import Log


class F5ProfilesController(CustomController):
    @staticmethod
    def get(request: Request, assetId: int, partitionName: str, profileType: str = "") -> Response:
        data = {"data": dict()}
        itemData = dict()
        etagCondition = { "responseEtag": "" }

        user = CustomController.loggedUser(request)

        try:
            if Permission.hasUserPermission(groups=user["groups"], action="profiles_get", assetId=assetId, partition=partitionName) or user["authDisabled"]:
                Log.actionLog("Profiles list", user)

                lock = Lock("profile", locals())
                if lock.isUnlocked():
                    lock.lock()

                    if profileType:
                        if profileType != "ANY":
                            # Profiles' list of that type.
                            # F5 treats profile type as a sub-object instead of a property. Odd.
                            itemData["items"] = Profile.list(assetId, partitionName, profileType)
                            data["data"] = ProfilesSerializer(itemData).data
                        else:
                            profileTypes = Profile.types(assetId, partitionName)

                            # The threading way.
                            # This requires a consistent throttle on remote appliance.
                            def profilesListOfType(pType):
                                itemData["items"] = Profile.list(assetId, partitionName, pType)
                                data["data"][pType] = ProfilesSerializer(itemData).data

                            workers = [threading.Thread(target=profilesListOfType, args=(m,)) for m in profileTypes]
                            for w in workers:
                                w.start()
                            for w in workers:
                                w.join()
                    else:
                        # Profiles' types list.
                        # No need for a serializer: just a list of strings.
                        data["data"]["items"] = Profile.types(assetId, partitionName)

                    data["href"] = request.get_full_path()

                    # Check the response's ETag validity (against client request).
                    conditional = Conditional(request)
                    etagCondition = conditional.responseEtagFreshnessAgainstRequest(data["data"])
                    if etagCondition["state"] == "fresh":
                        data = None
                        httpStatus = status.HTTP_304_NOT_MODIFIED
                    else:
                        httpStatus = status.HTTP_200_OK

                    lock.release()
                else:
                    data = None
                    httpStatus = status.HTTP_423_LOCKED
            else:
                data = None
                httpStatus = status.HTTP_403_FORBIDDEN
        except Exception as e:
            Lock("profile", locals()).release()

            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(data, status=httpStatus, headers={
            "ETag": etagCondition["responseEtag"],
            "Cache-Control": "must-revalidate"
        })



    @staticmethod
    def post(request: Request, assetId: int, partitionName: str, profileType: str) -> Response:
        response = None
        user = CustomController.loggedUser(request)

        try:
            if Permission.hasUserPermission(groups=user["groups"], action="profiles_post", assetId=assetId, partition=partitionName) or user["authDisabled"]:
                Log.actionLog("Profile addition", user)
                Log.actionLog("User data: "+str(request.data), user)

                serializer = ProfileSerializer(data=request.data["data"])
                if serializer.is_valid():
                    data = serializer.validated_data
                    data["partition"] = partitionName

                    lock = Lock("profile", locals(), profileType+data["name"])
                    if lock.isUnlocked():
                        lock.lock()

                        Profile.add(assetId, profileType, data)

                        httpStatus = status.HTTP_201_CREATED
                        lock.release()
                    else:
                        httpStatus = status.HTTP_423_LOCKED
                else:
                    httpStatus = status.HTTP_400_BAD_REQUEST
                    response = {
                        "F5": {
                            "error": str(serializer.errors)
                        }
                    }

                    Log.actionLog("User data incorrect: "+str(response), user)
            else:
                httpStatus = status.HTTP_403_FORBIDDEN
        except Exception as e:
            if "serializer" in locals():
                Lock("profile", locals(), profileType+locals()["serializer"].data["name"]).release()

            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(response, status=httpStatus, headers={
            "Cache-Control": "no-cache"
        })
