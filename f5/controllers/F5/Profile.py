from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from f5.models.F5.Profile import Profile
from f5.models.Permission.Permission import Permission

from f5.serializers.F5.Profile import F5ProfileSerializer as Serializer

from f5.controllers.CustomController import CustomController

from f5.helpers.Lock import Lock
from f5.helpers.Log import Log


class F5ProfileController(CustomController):
    @staticmethod
    def delete(request: Request, assetId: int, partitionName: str, profileType: str, profileName: str) -> Response:
        user = CustomController.loggedUser(request)

        try:
            if Permission.hasUserPermission(groups=user["groups"], action="profile_delete", assetId=assetId, partition=partitionName) or user["authDisabled"]:
                Log.actionLog("Profile deletion", user)

                lock = Lock("profile", locals(), profileType+profileName)
                if lock.isUnlocked():
                    lock.lock()

                    Profile(assetId, partitionName, profileType, profileName).delete()

                    httpStatus = status.HTTP_200_OK
                    lock.release()
                else:
                    httpStatus = status.HTTP_423_LOCKED
            else:
                httpStatus = status.HTTP_403_FORBIDDEN
        except Exception as e:
            Lock("profile", locals(), profileType+profileName).release()

            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(None, status=httpStatus, headers={
            "Cache-Control": "no-cache"
        })



    @staticmethod
    def patch(request: Request, assetId: int, partitionName: str, profileType: str, profileName: str) -> Response:
        response = None
        user = CustomController.loggedUser(request)

        try:
            if Permission.hasUserPermission(groups=user["groups"], action="profile_patch", assetId=assetId, partition=partitionName) or user["authDisabled"]:
                Log.actionLog("Profile modification", user)
                Log.actionLog("User data: "+str(request.data), user)

                serializer = Serializer(data=request.data["data"], partial=True)
                if serializer.is_valid():
                    data = serializer.validated_data

                    lock = Lock("profile", locals(), profileType+profileName)
                    if lock.isUnlocked():
                        lock.lock()

                        Profile(assetId, partitionName, profileType, profileName).modify(data)

                        httpStatus = status.HTTP_200_OK
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
            Lock("profile", locals(), profileType+profileName).release()

            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(response, status=httpStatus, headers={
            "Cache-Control": "no-cache"
        })
