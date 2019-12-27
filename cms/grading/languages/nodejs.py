#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2016-2018 Stefano Maggiolo <s.maggiolo@gmail.com>
# Copyright © 2019 Arthur Tondereau <arthurtondereau@gmail.com>
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

"""Node JS programming language, definition."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins.disabled import *  # noqa
from future.builtins import *  # noqa

import os

from cms.grading import CompiledLanguage


__all__ = ["NodeJS"]


class NodeJS(CompiledLanguage):
    """This defines the NodeJS programming language (the version of Node available on the system)
    using the default interpeter in the system.

    """

    @property
    def name(self):
        """See Language.name."""
        return "NodeJS"

    @property
    def source_extensions(self):
        """See Language.source_extensions."""
        return [".js"]

    def get_compilation_commands(self,
                                 source_filenames, executable_filename,
                                 for_evaluation=True):
        """See Language.get_compilation_commands."""
        # will only work for one source file, pass otherwise
        commands = []
        if len(source_filenames) != 1:
            commands.append(['rm ' + executable_filename])
        else:
            commands.append(
                ["/bin/mv", source_filenames[0], executable_filename])
        return commands

    def get_evaluation_commands(
            self, executable_filename, main=None, args=None):
        """See Language.get_evaluation_commands."""
        args = args if args is not None else []
        return [["/usr/bin/node", executable_filename] + args]
