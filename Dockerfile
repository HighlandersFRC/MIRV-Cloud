# 
FROM python:3.9

# 
WORKDIR /code/app

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app
# COPY ./app/schemas /code/app/schemas
# COPY ./app/main.py /code/app
# COPY ./app/main.py /code/app
# COPY ./app/rover_state.py /code/app
# COPY ./app/schemas/mirv_state_schemas.json /code/app

ENV KEYCLOAK_ENDPOINT=http://52.185.91.226:8080
ENV KEYCLOAK_REALM=vtti
ENV KEYCLOAK_CLIENT_USERS=users
ENV KEYCLOAK_CLIENT_DEVICES=devices
ENV KEYCLOAK_SECRET_KEY=0hUM7b7LWhHp8s0JMdBy4TkF18eLBajB

# 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 