# Copyright 2023 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##
# Base stage
#
FROM node:16.16 AS base

WORKDIR /app

COPY package.json /app/package.json
RUN npm install

COPY . /app

##
# Development stage
#
FROM base AS dev
CMD npm run start -- --watch --hmr --live-reload --host 0.0.0.0 --port $PORT

##
# Builder stage
#
FROM base AS builder
RUN npm run build -- -c production

##
# Production stage
#
FROM nginx:stable AS prod
COPY --from=builder /app/dist/ /var/www
COPY ./nginx.conf /etc/nginx/conf.d/configfile.template
CMD sh -c "envsubst '\$PORT,\$APP_TITLE' < /etc/nginx/conf.d/configfile.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"