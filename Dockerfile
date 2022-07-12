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
COPY ./app/main.py /code/app
COPY ./app/log.ini /code/app
COPY ./app/main.py /code/app
COPY ./app/rover_state.py /code/app
COPY ./app/schemas/mirv_schemas.py /code/app
# 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"] 