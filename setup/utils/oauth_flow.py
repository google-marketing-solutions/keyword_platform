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

"""Binary to go through the OAuth Flow.

The binary is intended to be run from a shell script, hence print statements are
used instead of logging statements. The result of going through the flow is a
refresh token that is stored in a text file, so it can be picked up from within
the shell script.
"""

from collections.abc import Sequence
import os
from typing import Union
import urllib

from absl import app
from absl import flags
import google_auth_oauthlib
import oauthlib.oauth2.rfc6749.errors as auth_errors

_CLIENT_ID = flags.DEFINE_string('client_id', None, 'Client ID.', required=True)

_CLIENT_SECRET = flags.DEFINE_string(
    'client_secret', None, 'Client secret.', required=True
)

_STATE = flags.DEFINE_string('state', None, 'State.', required=False)


_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-translation',
    'https://www.googleapis.com/auth/adwords',
]

_REDIRECT_URI = 'http://localhost:8080'


class OAuthFlow:
  """A class to run the OAuth2 Flow.

  The class can be used to generate a refresh token by launching an interative
  process to obtain the authorization code after gaining user consent for the
  required scopes.

  Example Usage:
    oauth_flow = OAuthFlow(client_id, client_secret)
    refresh_token = oauth_flow.generate_refresh_token()
  """

  def __init__(
      self, client_id: str, client_secret: str, state: Union[str, None] = None
  ) -> None:
    """Constructor.

    Args:
      client_id: A Web Client ID.
      client_secret: A Web Client Secret.
      state: A state that should can be added to the flow to prevent XSRF.
    """
    self._client_id = client_id
    self._client_secret = client_secret
    self._state = state
    self._flow = self._build_flow()

  def _build_flow(self) -> google_auth_oauthlib.flow.Flow:
    """Builds and returns OAuth2 flow.

    Returns:
        An instance of google_auth_oauthlib.flow.Flow.
    """
    return google_auth_oauthlib.flow.Flow.from_client_config(
        {
            'web': {
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
            },
        },
        scopes=_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=self._state,
    )

  def get_refresh_token_from_flow(self) -> str:
    """Launches an interacitive process obtain an OAuth2.0 refresh token.

    Returns:
      A refresh token.

    Raises:
      InvalidGrantError: If the grant was invalid.
      MissingCodeError: If flow is missing the authorization code.
    """
    authorization_url, _ = self._flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true',
        prompt='consent',
    )
    print('\n-----------------------------------------------------------')
    print(
        'Log into the Google Account you use to access your AdWords account '
        f'and go to the following URL: \n{authorization_url}\n'
    )
    print('-----------------------------------------------------------')
    print(
        'After approving you will ecounter ERR_CONNECTION_REFUSED - This is '
        'expected.'
    )
    print('Copy and paste the full URL from your browsers address bar.')
    url = input('URL: ').strip()
    code = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['code'][0]
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    try:
      self._flow.fetch_token(code=code)
    except (auth_errors.InvalidGrantError, auth_errors.MissingCodeError) as err:
      print(f'Authentication has failed: {err}')
      raise err
    return self._flow.credentials.refresh_token


def _write_refresh_token_to_file(refresh_token: str) -> None:
  """Writes a refresh token to a file.

  Args:
    refresh_token: The refresh token.
  """
  with open('refresh_token.txt', 'w') as f:
    f.write(refresh_token)


def main(argv: Sequence[str]) -> None:
  del argv

  refresh_token = OAuthFlow(
      _CLIENT_ID.value, _CLIENT_SECRET.value, _STATE.value
  ).get_refresh_token_from_flow()
  _write_refresh_token_to_file(refresh_token)


if __name__ == '__main__':
  app.run(main)
