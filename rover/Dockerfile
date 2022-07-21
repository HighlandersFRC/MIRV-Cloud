# 
FROM python:3.9

# 
WORKDIR /code/app

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


# 
COPY ./app /code/app
# COPY ./app/schemas /code/app/schemas
# COPY ./app/main.py /code/app
# COPY ./app/main.py /code/app
# COPY ./app/rover_state.py /code/app
# COPY ./app/schemas/mirv_state_schemas.json /code/app

ENV CLOUD_ENDPOINT=20.12.173.228
ENV ROVER_ID=rover_22

# 
CMD ["python", "MockRover.py"] 