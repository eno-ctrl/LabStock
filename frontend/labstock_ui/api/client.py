from typing import Any

import httpx

from frontend.labstock_ui.config import API_BASE_URL
from frontend.labstock_ui.state.session import session


class ApiClientException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 12.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self, custom_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if session.access_token:
            headers["Authorization"] = f"Bearer {session.access_token}"
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def _parse_error(self, response: httpx.Response) -> ApiClientException:
        try:
            body = response.json()
            if isinstance(body, dict) and "error" in body:
                err = body["error"]
                return ApiClientException(
                    code=err.get("code", "API_ERROR"),
                    message=err.get("message", response.text),
                    status_code=response.status_code,
                    details=err.get("details"),
                )
        except Exception:
            pass

        return ApiClientException(
            code=f"HTTP_{response.status_code}",
            message=response.text or f"Server returned error status {response.status_code}",
            status_code=response.status_code,
        )

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_data,
                    headers=self._headers(headers),
                )
                if resp.status_code == 401:
                    session.logout()
                    raise self._parse_error(resp)

                if resp.is_error:
                    raise self._parse_error(resp)

                if resp.headers.get("content-type", "").startswith("text/csv"):
                    return resp.text

                if resp.status_code == 204 or not resp.content:
                    return None

                return resp.json()
        except httpx.ConnectError as err:
            raise ApiClientException(
                code="BACKEND_UNAVAILABLE",
                message="Cannot connect to LabStock backend service. Please ensure the server is running on port 8000.",
                status_code=503,
            ) from err
        except httpx.TimeoutException as err:
            raise ApiClientException(
                code="REQUEST_TIMEOUT",
                message="Request timed out while waiting for server response.",
                status_code=504,
            ) from err

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, json_data: Any | None = None) -> Any:
        return self.request("POST", path, json_data=json_data)

    def patch(self, path: str, json_data: Any | None = None) -> Any:
        return self.request("PATCH", path, json_data=json_data)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)


api_client = ApiClient()
