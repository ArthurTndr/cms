#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Contest Management System - http://cms-dev.github.io/
# Copyright © 2016-2017 Stefano Maggiolo <s.maggiolo@gmail.com>
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

"""Kotlin programming language definition.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future.builtins.disabled import *
from future.builtins import *

from cms.grading import Language


__all__ = ["Kotlin"]


class Kotlin(Language):
    """This defines the Kotlin programming language, compiled into jar and
    executed using Java.

    """

    @property
    def name(self):
        """See Language.name."""
        return "Kotlin / JDK"

    @property
    def source_extensions(self):
        """See Language.source_extensions."""
        return [".kt"]

    @property
    def requires_multithreading(self):
        """See Language.requires_multithreading."""
        return True

    def get_compilation_commands(self,
                                 source_filenames, executable_filename,
                                 for_evaluation=True):
        """See Language.get_compilation_commands."""
        # We need to let the shell expand *.class as javac create
        # a class file for each inner class.
        compile_command = ["/usr/bin/kotlinc", source_filenames, "-include-runtime",
                           "-d", "%s.jar" % executable_filename]
        mv_command = ["/bin/mv",
                      "%s.jar" % executable_filename,
                      executable_filename]
        return [compile_command, mv_command]
    #kotlinc hello.kt -include-runtime -d hello.jar

    def get_evaluation_commands(
            self, executable_filename, main=None, args=None):
        """See Language.get_evaluation_commands."""
        args = args if args is not None else []
        # executable_filename is a jar file, main is the name of
        # the main java class
        return [["/usr/bin/java", "-Xmx512M", "-Xss64M", "-jar",
                 executable_filename] + args]
