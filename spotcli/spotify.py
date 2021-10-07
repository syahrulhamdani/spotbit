"""Spotify Web API Client in Python"""
import os
from base64 import b64encode
from http import HTTPStatus
from time import time

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3 import Retry

from .config import CLIENT_ID, CLIENT_SECRET, TOKEN_URL
from .exception import SpotbitException, ClientException


class Spotify:
    """Spotify object interface.

    1. SPOTBIT_CLIENT_ID and SPOTIBT_CLIENT_SECRET
    2. Encode them using base64
    3. Authorize to get access token
    """
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
    ):
        """Instantiate Spotify client.

        Client ID and secret can be specified as environment variables. If it
        does, you can skip passing parameters.

        Args:
            client_id (str): spotify Client ID. Either pass directly or define
                as an environment variable. Default is `None`.
            client_secret (str): spotify Client Secret. Either pass directly
                or define as an environment variable. Default is `None`.
        """
        self.client_id = client_id
        if not client_id:
            if not CLIENT_ID:
                raise ClientException(
                    f"Got Client ID {CLIENT_ID}."
                    f" Either specify as env variables or pass it directly."
                )
            self.client_id = CLIENT_ID

        self.client_secret = client_secret
        if not client_secret:
            if not CLIENT_SECRET:
                raise ClientException(
                    f"Got Client Secret {CLIENT_SECRET}."
                    f" Either specify as env variables or pass it directly."
                )
            self.client_secret = CLIENT_SECRET

    def _encode(self):
        byte = bytes(
            self.client_id + ":" + self.client_secret, encoding="utf-8"
        )
        return b64encode(byte).decode()

    @property
    def session(self) -> requests.Session:
        """
        Returns:
            requests.Session
        """
        if not hasattr(self, "_session"):
            session = requests.Session()
            retries = Retry(
                total=5,
                backoff_factor=0.1,
                status_forcelist=[
                    HTTPStatus.REQUEST_TIMEOUT,
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    HTTPStatus.BAD_GATEWAY,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.GATEWAY_TIMEOUT,
                ]
            )
            adapter = HTTPAdapter(
                max_retries=retries,
                pool_connections=(os.cpu_count() or 1) * 5,
                pool_maxsize=(os.cpu_count() or 1) * 5,
            )
            # session.mount('http://', adapter)
            session.mount('https://', adapter)
            setattr(self, "_session", session)
        return getattr(self, "_session")

    @property
    def token(self):
        """Authenticate and get access tokens."""
        def _get_token(data, headers):
            try:
                res = self.session.post(
                    TOKEN_URL, data=data, headers=headers
                )
                token = res.json()
                res.raise_for_status()
            except RequestException:
                raise SpotbitException("Got error when trying to acquire token")
            return token

        now = time()
        headers = {
            "Authorization": f"Basic {self._encode()}"
        }
        data = {
            "grant_type": "client_credentials"
        }

        if not hasattr(self, "_token"):
            token = _get_token(data=data, headers=headers)
            setattr(self, "_token", token.get("access_token"))
            setattr(self, "_expires_in", token.get("expires_in") + now)
            return getattr(self, "_token")

        token_expired = now > getattr(self, "_expires_in")
        if token_expired:
            token = _get_token(data=data, headers=headers)
            setattr(self, "_token", token.get("access_token"))
            setattr(self, "_expires_in", token.get("expires_in") + now)
        return getattr(self, "_token")
