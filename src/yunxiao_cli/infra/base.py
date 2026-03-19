from __future__ import annotations

from typing import Any

import requests


class YunxiaoAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class BaseAPI:
    BASE_URL = "https://openapi-rdc.aliyuncs.com"

    def __init__(self, token: str):
        if not token:
            raise YunxiaoAPIError("missing yunxiao token")
        self.token = token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        response = requests.request(
            method=method,
            url=f"{self.BASE_URL}{path}",
            params=params,
            json=data,
            headers={
                "x-yunxiao-token": self.token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
        )
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: requests.Response) -> Any:
        if response.status_code >= 400:
            payload = {}
            try:
                payload = response.json()
            except Exception:
                payload = {"message": response.text}
            raise YunxiaoAPIError(
                payload.get("errorMessage") or payload.get("message") or response.text,
                status_code=response.status_code,
                response=payload,
            )
        if not response.content:
            return {}
        return response.json()

    def _request_multipart(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        response = requests.request(
            method=method,
            url=f"{self.BASE_URL}{path}",
            data=data,
            files=files,
            headers={
                "x-yunxiao-token": self.token,
                "Accept": "application/json",
            },
            timeout=30,
        )
        return self._parse_response(response)

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return self._request("POST", path, params=params, data=data)

    def put(self, path: str, *, data: dict[str, Any] | None = None) -> Any:
        return self._request("PUT", path, data=data)

    def post_multipart(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        return self._request_multipart("POST", path, data=data, files=files)
