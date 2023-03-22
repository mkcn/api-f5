import functools

from django.conf import settings
from django.http import HttpRequest
from rest_framework.request import Request

from f5.models.F5.Asset.Asset import Asset

from f5.helpers.Log import Log


if not hasattr(settings, "ENABLE_ASSET_DR") or not settings.ENABLE_ASSET_DR:
    def AssetDr(func): # null decorator.
        return func
else:
    class AssetDr:
        def __init__(self, wrappedMethod: callable, *args, **kwargs) -> None:
            self.wrappedMethod = wrappedMethod
            self.primaryAssetId: int = 0
            self.assets = list() # dr asset ids list.



        ####################################################################################################################
        # Public methods
        ####################################################################################################################

        def __call__(self, request: Request, **kwargs):
            @functools.wraps(request)
            def wrapped():
                responses = list()

                try:
                    # Perform the request to the primary asset.
                    result = self.wrappedMethod(request, **kwargs)
                    responses.append(result)

                    if result.status_code in (200, 201, 202, 204): # reply the action in dr only if it was successful.
                        if "dr" in request.query_params and request.query_params["dr"]: # reply action in dr only if dr=1 param was passed.
                            self.primaryAssetId = int(kwargs["assetId"])
                            for asset in self.__assetsDr():
                                try:
                                    # Modify the request injecting the dr asset and re-run the decorated method.
                                    req = AssetDr.__copyRequest(request)
                                    kwargs["assetId"] = asset.get("id", 0)

                                    responses.append(self.wrappedMethod(req, **kwargs))
                                except Exception as e:
                                    raise e

                    return responses[0]
                except Exception as e:
                    raise e

            return wrapped()



        ####################################################################################################################
        # Private methods
        ####################################################################################################################

        def __assetsDr(self) -> list:
            l = list()

            try:
                if self.primaryAssetId:
                    l = Asset(self.primaryAssetId).drDataList(onlyEnabled=True)

                return l
            except Exception as e:
                raise e



        @staticmethod
        def __copyRequest(request: Request) -> Request:
            try:
                djangoHttpRequest = HttpRequest()
                djangoHttpRequest.path = request.path[:]
                djangoHttpRequest.query_params = request.query_params.copy()
                for attr in ("POST", "data", "FILES", "auth", "META"):
                    setattr(djangoHttpRequest, attr, getattr(request, attr))

                req = Request(djangoHttpRequest)
                for attr in ("authenticators", "accepted_media_type", "accepted_renderer", "version", "versioning_scheme"):
                    setattr(req, attr, getattr(request, attr))

                return req
            except Exception as e:
                raise e