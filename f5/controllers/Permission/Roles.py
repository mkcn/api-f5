from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from f5.models.Permission.Role import Role
from f5.models.Permission.Permission import Permission

from f5.serializers.Permission.Roles import RolesSerializer as Serializer

from f5.controllers.CustomController import CustomController
from f5.helpers.Conditional import Conditional
from f5.helpers.Log import Log


class PermissionRolesController(CustomController):
    @staticmethod
    def get(request: Request) -> Response:
        data = dict()
        loadPrivilege = False
        etagCondition = {"responseEtag": ""}

        user = CustomController.loggedUser(request)

        try:
            if Permission.hasUserPermission(groups=user["groups"], action="permission_roles_get") or user["authDisabled"]:
                Log.actionLog("Roles list", user)

                # If asked for, get related privileges.
                if "related" in request.GET:
                    rList = request.GET.getlist('related')
                    if "privileges" in rList:
                        loadPrivilege = True

                data = {
                    "data": {
                        "items": CustomController.validate(
                            Role.dataList(loadPrivilege=loadPrivilege),
                            Serializer,
                            "list"
                        )
                    },
                    "href": request.get_full_path()
                }

                # Check the response's ETag validity (against client request).
                conditional = Conditional(request)
                etagCondition = conditional.responseEtagFreshnessAgainstRequest(data["data"])
                if etagCondition["state"] == "fresh":
                    data = None
                    httpStatus = status.HTTP_304_NOT_MODIFIED
                else:
                    httpStatus = status.HTTP_200_OK
            else:
                data = None
                httpStatus = status.HTTP_403_FORBIDDEN
        except Exception as e:
            data, httpStatus, headers = CustomController.exceptionHandler(e)
            return Response(data, status=httpStatus, headers=headers)

        return Response(data, status=httpStatus, headers={
            "ETag": etagCondition["responseEtag"],
            "Cache-Control": "must-revalidate"
        })
