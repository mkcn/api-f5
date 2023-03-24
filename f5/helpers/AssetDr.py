import functools
import json

from django.conf import settings
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.response import Response

from f5.models.F5.Asset.Asset import Asset
from f5.models.History.HistoryDr import HistoryDr
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

                try:
                    self.primaryAssetId = int(kwargs["assetId"])

                    # Perform the request to the primary asset.
                    responsePr = self.wrappedMethod(request, **kwargs)


                    if responsePr.status_code in (200, 201, 202, 204): # reply the action in dr only if it was successful.
                        if "dr" in request.query_params and request.query_params["dr"]: # reply action in dr only if dr=1 param was passed.

                            for asset in self.__assetsDr():
                                try:
                                    # Modify the request injecting the dr asset and re-run the decorated method.
                                    req = AssetDr.__copyRequest(request)
                                    kwargs["assetId"] = asset.get("id", 0)

                                    historyId = self.__historyPrepare(request=request, response=responsePr, drAssetId=kwargs["assetId"], drAssetFqdn=asset.get("fqdn", 0))
                                    responseDr = self.wrappedMethod(req, **kwargs)
                                    self.__historyDr(historyId=historyId, response=responseDr)
                                except Exception as e:
                                    raise e

                    return responsePr
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



        def __historyPrepare(self, request: Request, response: Response, drAssetId: int, drAssetFqdn: str) -> int:
            try:
                reqestData = {
                        "path": request.path,
                        "method": request.method,
                        "data": request.data,
                        "params": request.query_params
                    }

                return HistoryDr.add({
                    "pr_asset_id":  int(self.primaryAssetId),
                    "dr_asset_id": drAssetId,
                    "dr_asset_fqdn": drAssetFqdn,
                    "username": "",
                    "request": json.dumps(reqestData),
                    "pr_status": response.status_code,
                    "dr_status": "",
                    "pr_response": json.dumps(response.data),
                    "dr_response": ""
                })

            except Exception as e:
                raise e



        def __historyDr(self, historyId: int, response: Response) -> None:
            try:
                HistoryDr(id=historyId).modify({
                    "dr_status": response.status_code,
                    "dr_response": json.dumps(response.data)
                })

            except Exception:
                pass




        ####################################################################################################################
        # Private static methods
        ####################################################################################################################

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

