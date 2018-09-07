#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# By Thomas Lacroix, with no warranty.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import io
import logging
import os
import string
import csv
from datetime import timedelta

from cms.db import User
from cmscommon.crypto import build_password
from cmscontrib.loaders import YamlLoader

logger = logging.getLogger(__name__)


def make_timedelta(t):
    return timedelta(seconds=t)


def random_password(length=10):
    chars = (
        string.ascii_uppercase + string.digits + string.ascii_lowercase
        + '_-')
    password = ''
    for i in range(length):
        password += chars[ord(os.urandom(1)) % len(chars)]
    return password


# Code from https://docs.python.org/2.7/library/csv.html#examples
def unicode_csv_reader(unicode_csv_data, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            delimiter=str(','),
                            quotechar=str('"'),
                            **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


class ShakerUserLoader(YamlLoader):
    """Load users stored using the Shaker format.
    """

    short_name = 'shaker_format'
    description = 'Shaker format based on Italian, with CSV-based user format'

    @staticmethod
    def detect(path):
        """See docstring in class Loader.
        """
        return os.path.exists(
            os.path.join(os.path.dirname(path), "users.csv"))

    def user_has_changed(self):
        """See docstring in class Loader.
        """
        return True

    def get_user_loader(self, username):
        return ShakerUserLoader(
            os.path.join(self.path, username), self.file_cacher)

    def get_user(self):
        """See docstring in class Loader.
        """

        username = os.path.basename(self.path)
        userdata = None

        # Shaker user format (CSV-based):
        #
        # This is not standard Polygon feature, but useful for CMS users
        # we assume contestants.txt contains one line for each user, and
        # a header line, as follow:
        #
        # ...,Prénom,Nom,Pseudo,Mot de passe,...
        # (additionnal columns are accepted, and order isn't important)
        #

        users_path = os.path.join(
            os.path.dirname(self.path), 'contestants.csv')
        if not os.path.exists(users_path):
            users_path = os.path.join(
                os.path.dirname(self.path), '../contestants.csv')
        if not os.path.exists(users_path):
            logger.critical("contestants.csv not found!")
            exit(1)
            return None

        try:
            headers = dict()
            if os.path.exists(users_path):
                with io.open(users_path, "rt", encoding="utf-8") as users_file:
                    reader = unicode_csv_reader(users_file)

                    # Headers
                    headers_list = next(reader)
                    headers = dict(zip(headers_list, range(len(headers_list))))

                    # Content
                    for user in reader:
                        if len(user) == 0:
                            continue
                        name = user[headers['Pseudo']].strip()
                        if name == username:
                            userdata = [x.strip() for x in user]
                            break

            def get_param(param, default=None):
                try:
                    return userdata[headers[param]]
                except KeyError as _:
                    if default is None:
                        raise _
                    return default

            if userdata is not None:
                logger.info("Loading parameters for user %s.", username)
                args = {
                    'username': get_param('Pseudo'),
                    'password': get_param('Mot de passe', ''),
                    'first_name': get_param('Prénom', ''),
                    'last_name': get_param('Nom', '')
                }
                # args['hidden'] = get_param('hidden', False) == '1'

                # Generate a password if none is defined
                if len(args['password']) == 0:
                    args['password'] = random_password()

                # Build an auth string from the password
                args['password'] = build_password(args['password'])

                logger.info("User parameters loaded.")
                return User(**args)
            else:
                logger.critical(
                    "User %s not found in contestants.csv file.", username)
                exit(1)
                return None
        except KeyError as e:
            logger.critical(
                "contestants.csv is ill-formed: column %s not found!", e)
            exit(1)
            return None

    def get_contest(self):
        """See docstring in class Loader."""

        # See get_user() for file format

        participations = []
        try:
            users_path = os.path.join(
                os.path.dirname(self.path) + "/contestants.csv")
            searched_locations = []
            if not os.path.exists(users_path):
                searched_locations.append(users_path)
                users_path = os.path.join(self.path + "/contestants.csv")
            if not os.path.exists(users_path):
                searched_locations.append(users_path)
                users_path = os.path.join(
                    os.path.dirname(self.path), "../contestants.csv")
            if not os.path.exists(users_path):
                searched_locations.append(users_path)
                logger.warning(
                    "contestants.csv not found! (searched in %s, %s and %s)",
                    *searched_locations)
                logger.warning("Participations won't be loaded.")

            if os.path.exists(users_path):
                # Read contestants
                with io.open(users_path, str("rt"), encoding=str("utf-8")) \
                        as users_file:
                    reader = unicode_csv_reader(users_file)

                    # Headers
                    headers_list = next(reader)
                    headers = dict(zip(headers_list, range(len(headers_list))))

                    # Content
                    for user in reader:
                        if len(user) == 0:
                            continue
                        name = user[headers['Pseudo']].strip()
                        if name == '':
                            continue
                        participations.append({u'username': name})

        except KeyError as e:
            logger.critical(
                "contestants.csv is ill-formed: column %s not found!", e)
            exit(1)
            return None

        logger.info("Participations loaded (%d users).", len(participations))

        # Load contest from the Italian format
        contest, tasks, _ = super(ShakerUserLoader, self).get_contest()

        return contest, tasks, participations

    def contest_has_changed(self):
        """See docstring in class ContestLoader."""
        return True
