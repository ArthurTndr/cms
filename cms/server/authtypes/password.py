#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Programming contest management system
# Copyright © 2013 Bernard Blackham <b-cms@largestprime.net>
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

import logging
import ipaddress

from cms.server.authtype import AuthType
from cms.server.contest.authentication import validate_login
from cms.server.contest.handlers.contest import ContestHandler


logger = logging.getLogger(__name__)


class Password(AuthType):
    """This is the base authentication method with username and password
    """
    @classmethod
    def get_login_html(self, **kwargs):
        """Return the path to the html file to insert in the login page.
        """
        return "auth_password"

    @staticmethod
    def get_url_handlers():
        return [
            (r"/login", LoginHandler),
        ]


class LoginHandler(ContestHandler):
    """Login handler.
    """
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        try:
            # In py2 Tornado gives us the IP address as a native binary
            # string, whereas ipaddress wants text (unicode) strings.
            ip_address = ipaddress.ip_address(str(self.request.remote_ip))
        except ValueError:
            logger.info("Invalid IP address provided by Tornado: %s",
                        self.request.remote_ip)
            ip_address = None

        participation, cookie = validate_login(
            self.sql_session, self.contest, self.timestamp, username, password,
            ip_address)

        cookie_name = self.contest.name + "_login"
        if cookie is None:
            self.clear_cookie(cookie_name)
        else:
            self.set_secure_cookie(cookie_name, cookie, expires_days=None)

        if participation is None:
            self.redirect_login_error()
        else:
            self.redirect_next()
