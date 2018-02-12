#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# By Thomas Lacroix, with no warranty.

"""This service exports every data that CMS knows. The process of
exporting and importing again should be idempotent.

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# We enable monkey patching to make many libraries gevent-friendly
# (for instance, urllib3, used by requests)
import gevent.monkey

gevent.monkey.patch_all()

import argparse
import io
import json
import logging
import os
import sys

from cms import utf8_decoder
from cms.db import SessionGen, Contest
from cms.db.filecacher import FileCacher

from datetime import date

logger = logging.getLogger(__name__)


class UserExporter(object):
    """
    This service exports into HTML every users participating to a given contest.
    """

    def __init__(self, contest_id, export_target, json):
        self.contest_id = contest_id
        self.export_target = export_target
        self.json = json

        # If target is not provided, we use the curent date.
        if export_target == "":
            self.export_target = "users_c%d_%s.html" % \
                                 (self.contest_id, date.today().isoformat())
            logger.warning("export_target not given, using \"%s\"",
                           self.export_target)

        self.file_cacher = FileCacher()

    def do_export(self):
        """Run the actual export code."""
        logger.info("Starting export.")

        # Export users
        users = []
        with SessionGen() as session:
            # Get the contest
            contest = Contest.get_from_id(self.contest_id, session)
            if contest is None:
                logger.critical("Contest %d not found in database.", self.contest_id)
                exit(1)

            # Get participations of the contest
            participations = contest.participations
            for p in participations:
                users.append({
                    u'username': p.user.username,
                    u'password': p.user.password,
                    u'first_name': p.user.first_name,
                    u'last_name': p.user.last_name
                })

        if self.json:
            j = {'users': users}
            with io.open(os.path.join(self.export_target), "wb") as fout:
                json.dump(j, fout, encoding="utf-8", indent=2, sort_keys=True)
        else:
            html = """
            <table>
                <tr>
                    <th>Prénom</th>
                    <th>Nom</th>
                    <th>Pseudo</th>
                    <th>Mot de passe</th>
                </tr>
            """
            for u in users:
                html += """
                <tr>
                    <td>{first_name}</td>
                    <td>{last_name}</td>
                    <td>{username}</td>
                    <td>{password}</td>
                </tr>
                """.format(
                    first_name=u['first_name'],
                    last_name=u['last_name'],
                    username=u['username'],
                    password=u['password'],
                )
            html += "</table>"
            html = """
<!DOCTYPE html>
<html lang="fr">
    <head>
        <meta charset="utf-8">
        <title>Export des utilisateurs</title>
        <style>
table {{
    font-family: arial, sans-serif;
    border-collapse: separate;
    border-spacing: 0 1em;
    width: 100%;
}}
td, th {{
    border-top: 1px solid #dddddd;
    text-align: left;
    padding: 8px;
}}
        </style>
    </head>
    <body>
        {}
    </body>
</html>
            """.format(html)
            with io.open(os.path.join(self.export_target), "wb") as fout:
                fout.write(html.encode('utf8'))

        logger.info("Export finished.")
        return True


def main():
    """Parse arguments and launch process."""
    parser = argparse.ArgumentParser(description="Dump of users/password in HTML ou JSON format.")
    parser.add_argument(
        "contest_id",
        action="store", type=int,
        help="id of the contest the users will be attached to"
    )
    parser.add_argument(
        "export_target",
        action="store", type=utf8_decoder,
        nargs='?', default="",
        help="target HTML file"
    )
    parser.add_argument(
        "-j", "--json",
        action="store",
        help="export to JSON rather than HTML"
    )

    args = parser.parse_args()

    exporter = UserExporter(contest_id=args.contest_id,
                            export_target=args.export_target,
                            json=args.json)
    success = exporter.do_export()
    return 0 if success is True else 1


if __name__ == "__main__":
    sys.exit(main())
