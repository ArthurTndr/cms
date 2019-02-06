#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
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

"""Export the users' code and some info about their entry
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins.disabled import *  # noqa
from future.builtins import *  # noqa

# import csv
# import io
import zipfile
import logging

from cms.db import Contest, Submission, Task

from .base import BaseHandler, require_permission


logger = logging.getLogger(__name__)


class UsersData(BaseHandler):
    """
    """
    @require_permission(BaseHandler.AUTHENTICATED)
    def get(self, contest_id, format="online"):
        contest = self.safe_get_item(Contest, contest_id)
        self.contest = contest

        self.set_header("Content-Type", "application/zip")
        self.set_header("Content-Disposition",
                        "attachment; filename=\"users_data.zip\"")

        with open("test.txt", "w") as f:
            f.write("Hello World!")

        zfile = zipfile.ZipFile("users_data.zip", "w", zipfile.ZIP_DEFLATED)
        zfile.write("test.txt")

        zfile.close()
        output = open("users_data.zip", "rb", buffering=0)

        self.finish(output.read())
