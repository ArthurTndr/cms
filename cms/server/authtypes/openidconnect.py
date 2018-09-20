#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2018 Louis Sugy <contact@nyri0.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging
import ipaddress
import tornado.web

# pyoidc
from oic import rndstr
from oic.oic import Client
from oic.utils.keyio import KeyJar
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oic.message import ProviderConfigurationResponse, ClaimsRequest, \
    Claims, RegistrationResponse, AuthorizationResponse

from cms.db.user import User, Participation
from cms.server.authtype import AuthType
from cms.server.contest.authentication import validate_login
from cms.server.contest.handlers.contest import ContestHandler
from cmscommon.crypto import generate_random_password, build_password, \
    parse_authentication

# from cmscommon.DateTime import make_timestamp


logger = logging.getLogger(__name__)


class OpenIDConnect(AuthType):
    @classmethod
    def get_login_html(self, **kwargs):
        """Return the path to the html file to insert in the login page.
        """
        return "auth_oic"

    @staticmethod
    def get_url_handlers():
        return [
            (r"/oic_login", OpenIDConnectLoginHandler),
        ]

    @staticmethod
    def get_user_string(user):
        return "via OpenIDConnect"


class OpenIDConnectLoginHandler(ContestHandler):
    """OpenIDConnect login handler.

    """

    def create_client(self):
        """Create the OpenIDConnect client from the data stored in the contest
        object, and store some information in this handler object.
        """
        oic_info = json.loads(self.contest.openidconnect_info)
        self.redirect_uri = (
            self.request.protocol + "://" + self.request.host
            + self.request.path)
        self.op_info = oic_info["op_info"]
        self.client_info = oic_info["client_info"]
        self.client_info["redirect_uris"] = [self.redirect_uri]
        self.jwks = oic_info["jwks"]

        keyjar = KeyJar()
        keyjar.import_jwks(self.jwks, self.op_info["issuer"])

        self.client = Client(
            client_authn_method=CLIENT_AUTHN_METHOD, keyjar=keyjar)
        self.client.provider_info = \
            ProviderConfigurationResponse(**self.op_info)
        self.client.store_registration_info(
            RegistrationResponse(**self.client_info))

    @tornado.gen.coroutine
    def get(self):
        self.create_client()

        # When we have a code, request id token
        if self.get_argument('code', False):
            response = self.request.query
            response = self.client.parse_response(
                AuthorizationResponse, info=response,
                sformat="urlencoded")

            # The query is checked against the state in the cookie
            code = response['code'] if 'code' in response else None
            state = response['state'] if 'state' in response else None
            cookie = self.get_secure_cookie(self.contest.name + "_auth")
            if code and cookie and json.loads(cookie)[0] == state:
                args = {
                    "code": code,
                    "token_endpoint": self.op_info["token_endpoint"],
                    "redirect_uri": self.redirect_uri,
                }
                # Request an access token to the authentication server
                resp = yield self.get_access_token(
                    state=state,
                    request_args=args,
                    authn_method="client_secret_basic"
                )
            else:
                self.redirect_login_error()

            self.clear_cookie(self.contest.name + "_auth")

            # The token is checked against the nonce in the cookie
            id_token = resp["id_token"]
            if id_token["nonce"] != json.loads(cookie)[1]:
                self.redirect_login_error()

            first_name = id_token["given_name"]
            last_name = id_token["family_name"]
            email = id_token["email"]
            username = id_token["sub"]

            # Check if the user already exists
            user = self.sql_session.query(User)\
                .filter(User.username == username).first()

            # Create the user if it doesn't exist yet
            if user is None:
                user = User(
                    first_name, last_name, username, email=email,
                    password=build_password(generate_random_password()))
                self.sql_session.add(user)
                self.sql_session.commit()
            if not [p for p in user.participations
                    if p.contest_id == self.contest.id]:
                participation = Participation(
                    contest=self.contest, user=user)
                self.sql_session.add(participation)
                self.sql_session.commit()

            self.try_user_login(user)

        # Request a code
        else:
            state = rndstr()
            nonce = rndstr()
            self.set_secure_cookie(
                self.contest.name + "_auth",
                json.dumps([state, nonce]),
                expires_days=None)
            claims_request = ClaimsRequest(
                id_token=Claims(
                    sub={"essential": True}
                ),
                userinfo=Claims(
                    given_name={"essential": True},
                    family_name={"essential": True},
                    preferred_username={"essential": True},
                )
            )
            args = {
                "client_id": self.client.client_id,
                "response_type": "code",
                "scope": ["openid", "offline_access"],
                "nonce": nonce,
                "redirect_uri": self.redirect_uri,
                "state": state,
                "claims": claims_request,
            }
            next_page = self.get_argument('next', None)
            if next_page:
                args["next"] = next_page

            auth_req = (self.client.construct_AuthorizationRequest
                        (request_args=args))
            login_url = auth_req.request(
                self.op_info["authorization_endpoint"])
            self.redirect(login_url)

    @tornado.concurrent.return_future
    def get_access_token(self, callback, *args, **kwargs):
        res = self.client.do_access_token_request(*args, **kwargs)
        callback(res)

    def try_user_login(self, user):
        try:
            # In py2 Tornado gives us the IP address as a native binary
            # string, whereas ipaddress wants text (unicode) strings.
            ip_address = ipaddress.ip_address(str(self.request.remote_ip))
        except ValueError:
            logger.warning("Invalid IP address provided by Tornado: %s",
                           self.request.remote_ip)
            return None

        _, password = parse_authentication(user.password)
        participation, cookie = validate_login(
            self.sql_session, self.contest, self.timestamp, user.username,
            password, ip_address)

        cookie_name = self.contest.name + "_login"
        if cookie is None:
            self.clear_cookie(cookie_name)
        else:
            self.set_secure_cookie(cookie_name, cookie, expires_days=None)

        if participation is None:
            self.redirect_login_error()
        else:
            self.redirect_next()
