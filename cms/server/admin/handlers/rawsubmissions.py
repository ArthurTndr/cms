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

"""Export information about the submissions, for data mining
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins.disabled import *  # noqa
from future.builtins import *  # noqa
import six

import csv
import io
import logging

from cms.db import Contest, Submission, Task

from .base import BaseHandler, require_permission


logger = logging.getLogger(__name__)


class RawSubHandler(BaseHandler):
    """
    """
    @require_permission(BaseHandler.AUTHENTICATED)
    def get(self, contest_id, format="online"):
        contest = self.safe_get_item(Contest, contest_id)
        self.contest = contest

        submissions = self.sql_session.query(Submission).join(Task)\
            .filter(Task.contest == contest)

        self.set_header("Content-Type", "text/csv")
        self.set_header("Content-Disposition",
                        "attachment; filename=\"rawsubs.csv\"")

        if six.PY3:
            output = io.StringIO()  # untested
        else:
            # In python2 we must use this because its csv module does not
            # support unicode input
            output = io.BytesIO()
        writer = csv.writer(output)

        row = ["Time", "Username", "Task", "Status", "Language"]
        writer.writerow(row)

        for sub in submissions:
            sr = sub.get_result(sub.task.active_dataset)
            row = [
                str(sub.timestamp),
                sub.participation.user.username,
                sub.task.name,
                str(sr.score or 0),
                sub.language or "",
            ]

            if six.PY3:
                writer.writerow(row)  # untested
            else:
                writer.writerow([s.encode("utf-8") for s in row])

        self.finish(output.getvalue())
