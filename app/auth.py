from typing import Union
from fastapi import HTTPException, status
from pydantic import BaseModel
from keycloak import KeycloakOpenID


class MirvKeycloakProvider():
    def __init__(self, KEYCLOAK_ENDPOINT, KEYCLOAK_REALM, KEYCLOAK_CLIENT, KEYCLOAK_SECRET_KEY):
        self.keycloak_openid = KeycloakOpenID(server_url=f"{KEYCLOAK_ENDPOINT}/auth/",
                                              client_id=KEYCLOAK_CLIENT,
                                              realm_name=KEYCLOAK_REALM,
                                              client_secret_key=KEYCLOAK_SECRET_KEY)

    def get_access_token(self, username: str, password: str):
        try:
            return self.keycloak_openid.token(username, password)
        except:
            return None

    def get_user_info(self, token):
        try:
            return self.keycloak_openid.userinfo(token)
        except:
            return False

    def validate_token(self, token):
        if not self.get_user_info(token):
            return False
        return True
