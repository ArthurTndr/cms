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
import os
import shutil
import logging
from collections import defaultdict

from sqlalchemy.orm import joinedload

from .base import BaseHandler, require_permission
from cms.db import Contest, Submission
from cms.db.filecacher import FileCacher
from cms.grading.scoring import task_score
from cms.grading.languagemanager import get_language

BASE_PATH = "users_data"
logger = logging.getLogger(__name__)


class UsersData(BaseHandler):
    """
    """
    @require_permission(BaseHandler.AUTHENTICATED)
    def get(self, contest_id, format="online"):
        self.contest = self.sql_session.query(Contest)\
            .filter(Contest.id == contest_id)\
            .options(joinedload('participations'))\
            .options(joinedload('participations.submissions'))\
            .options(joinedload('participations.submissions.token'))\
            .options(joinedload('participations.submissions.results'))\
            .first()

        self.set_header("Content-Type", "application/zip")
        self.set_header("Content-Disposition",
                        "attachment; filename=\"users_data.zip\"")

        shutil.rmtree(BASE_PATH, ignore_errors=True)

        fc = FileCacher()

        for p in self.contest.participations:
            path = "%s/%s/" % (BASE_PATH, p.user.username)
            os.makedirs(path)

            # Find the users' scores for each task
            scores = []
            for task in self.contest.tasks:
                t_score, _ = task_score(p, task)
                t_score = round(t_score, task.score_precision)
                scores.append(t_score)

            # Write a csv with some information on the participation
            info_csv = [["Username", "User"]]
            for task in self.contest.tasks:
                info_csv[0].append(task.name)
            full_name = "%s %s" % (p.user.first_name, p.user.last_name)
            info_csv.append([p.user.username, full_name])
            for t_score in scores:
                info_csv[1].append(str(t_score))
            with open("%sinfo.csv" % path, "w") as f:
                f.write("\n".join(",".join(row) for row in info_csv))

            # Identify all the files submitted by the user for each task
            task_sr = defaultdict(list)
            for sub in p.submissions:
                sub_sr = sub.get_result(sub.task.active_dataset)

                file = sub.files.items()[0][1]
                filename = file.filename
                if sub.language is not None:
                    filename = filename.replace(
                        ".%l", get_language(sub.language).source_extension)
                if sub_sr.score:
                    task_sr[sub.task_id].append(
                        (sub_sr.score, sub.timestamp, (filename, file.digest)))

            # Select the last file submitted with maximum score for each task
            task_last_best = [
                sorted(task_sr[tid], key=lambda x: (x[0], x[1]),
                       reverse=True)[0][2]
                for tid in task_sr
            ]

            # Write the selected file for each task
            for filename, digest in task_last_best:
                file_content = fc.get_file(digest).read()
                with open("%s%s" % (path, filename), "w") as f:
                    f.write(file_content.decode("utf8"))

        # Create a downloadable archive will all this data
        shutil.make_archive("users_data", "zip", ".", "users_data")

        output = open("users_data.zip", "rb", buffering=0)

        self.finish(output.read())
