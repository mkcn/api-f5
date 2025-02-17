from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from f5.models.Configuration.Configuration import Configuration
from f5.models.Permission.Permission import Permission

from f5.serializers.Configuration.Configuration import ConfigurationSerializer as Serializer

from f5.controllers.CustomController import CustomController
from f5.helpers.Log import Log


class ConfigurationController(CustomController):
    @staticmethod
    def get(request: Request, configType: str) -> Response:
        user = CustomController.loggedUser(request)

        try:
            Log.actionLog("Configuration read", user)

            data = {
                "data": CustomController.validate(
                    Configuration.getByType(configType),
                    Serializer,
                    "value"
                ),
                "href": request.get_full_path()
            }

            httpStatus = status.HTTP_200_OK
        except Exception as e:
            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(data, status=httpStatus, headers={
            "Cache-Control": "no-cache"
        })



    @staticmethod
    def put(request: Request, configType: str) -> Response:
        response = None
        user = CustomController.loggedUser(request)

        try:
            if Permission.hasUserPermission(groups=user["groups"], action="configuration_put") or user["authDisabled"]:
                Log.actionLog("Configuration modification", user)
                Log.actionLog("User data: "+str(request.data), user)

                serializer = Serializer(data=request.data["data"])
                if serializer.is_valid():
                    Configuration.rewriteByType(
                        configType,
                        serializer.validated_data
                    )

                    httpStatus = status.HTTP_200_OK
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
            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(response, status=httpStatus, headers={
            "Cache-Control": "no-cache"
        })
