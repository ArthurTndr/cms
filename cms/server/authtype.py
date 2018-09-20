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


class AuthType:
    """This class contains the basic infrastructure from which we can
    build an authentication type.
    """

    @classmethod
    def get_login_html(self, **kwargs):
        """Return the path to the html file to insert in the login page.
        """
        return ""

    @staticmethod
    def get_url_handlers():
        return []

    @staticmethod
    def get_user_string(user):
        return user.username
