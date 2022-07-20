from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from keycloak import KeycloakOpenID
import os


KEYCLOAK_ENDPOINT = os.getenv("KEYCLOAK_ENDPOINT")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT = os.getenv("KEYCLOAK_CLIENT")
KEYCLOAK_SECRET_KEY = os.getenv("KEYCLOAK_SECRET_KEY")

# Configure client
keycloak_openid = KeycloakOpenID(server_url=f"{KEYCLOAK_ENDPOINT}/auth/",
                                 client_id=KEYCLOAK_CLIENT,
                                 realm_name=KEYCLOAK_REALM,
                                 client_secret_key=KEYCLOAK_SECRET_KEY)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def validate_token(token):
    if not get_user_info(token):
        return False
    return True


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    access_token = get_access_token(form_data.username, form_data.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not get_user_info(access_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}
