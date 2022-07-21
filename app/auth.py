from typing import Union
from fastapi import HTTPException, status
from pydantic import BaseModel
from keycloak import KeycloakOpenID


class MirvKeycloakProvider():
    def __init__(self, KEYCLOAK_ENDPOINT, KEYCLOAK_REALM, KEYCLOAK_CLIENT_USERS, KEYCLOAK_CLIENT_DEVICES, KEYCLOAK_SECRET_KEY):
        self.keycloak_client_users = KeycloakOpenID(server_url=f"{KEYCLOAK_ENDPOINT}/auth/",
                                                    client_id=KEYCLOAK_CLIENT_USERS,
                                                    realm_name=KEYCLOAK_REALM,
                                                    client_secret_key=KEYCLOAK_SECRET_KEY)
        self.keycloak_client_devices = KeycloakOpenID(server_url=f"{KEYCLOAK_ENDPOINT}/auth/",
                                                      client_id=KEYCLOAK_CLIENT_USERS,
                                                      realm_name=KEYCLOAK_REALM,
                                                      client_secret_key=KEYCLOAK_SECRET_KEY)

    def get_access_token_user(self, username: str, password: str):
        try:
            return self.keycloak_client_users.token(username, password)
        except:
            return None

    def get_user_info_user(self, token):
        try:
            return self.keycloak_client_users.userinfo(token)
        except:
            return False

    def validate_token_user(self, token):
        if not self.get_user_info_user(token):
            return False
        return True

    def get_access_token_device(self, username: str, password: str):
        try:
            return self.keycloak_client_devices.token(username, password)
        except:
            return None

    def get_user_info_device(self, token):
        try:
            return self.keycloak_client_devices.userinfo(token)
        except:
            return False

    def validate_token_device(self, token):
        if not self.get_user_info_device(token):
            return False
        return True
