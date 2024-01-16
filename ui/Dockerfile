# Copyright 2024 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM node:16.16 AS builder

WORKDIR /app

# Install angular dependencies.
COPY package.json /app/package.json
RUN npm install

COPY . ./

# Build static files.
RUN npm run build -- -c production

FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY ./py ./py/
# Install production dependencies.
RUN cd ./py && pip install --require-hashes --no-cache-dir --no-deps -r requirements.txt && cd ..

# Copy static files to root.
COPY --from=builder /app/dist/ /var/www

# Run the web service on container startup. Here we use the gunicorn
# web server, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --chdir /app/py main:app
EXPOSE $PORT