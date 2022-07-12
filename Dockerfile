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
# COPY ./app/main.py /code/app
# COPY ./app/main.py /code/app
# COPY ./app/rover_state.py /code/app
# COPY ./app/schemas/mirv_schemas.py /code/app

ENV PASSWORD=PASSWORD
ENV KEYCLOAK_ENDPOINT=http://20.221.15.60:8080
ENV KEYCLOAK_REALM=vtti
ENV KEYCLOAK_CLIENT=mirv
ENV KEYCLOAK_SECRET_KEY=0hUM7b7LWhHp8s0JMdBy4TkF18eLBajB

# 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 