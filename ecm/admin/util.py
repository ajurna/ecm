# Copyright (c) 2010-2012 Robin Jarry
#
# This file is part of EVE Corporation Management.
#
# EVE Corporation Management is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# EVE Corporation Management is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# EVE Corporation Management. If not, see <http://www.gnu.org/licenses/>.

__date__ = '2012 3 23'
__author__ = 'diabeteman'

import subprocess
import shlex
import sys
import logging

#-------------------------------------------------------------------------------
def prompt(message, valid_list=None):
    value = None
    if valid_list is not None:
        while value not in valid_list:
            value = raw_input('%s %s ' % (message, valid_list))
    else:
        while not value:
            value = raw_input('%s ' % message)
    return value


#-------------------------------------------------------------------------------
def run_command(command_line, run_dir):
    log = get_logger()
    log.info('$ ' + command_line)

    exitcode = subprocess.call(shlex.split(command_line), cwd=run_dir, universal_newlines=True)

    if exitcode != 0:
        sys.exit(exitcode)

#-------------------------------------------------------------------------------
__logger__ = None
def get_logger():
    global __logger__
    if __logger__ is not None:
        return __logger__
    else:
        logger = logging.getLogger()
        console_hdlr = logging.StreamHandler(sys.stdout)
        console_hdlr.setFormatter(logging.Formatter('[ECM] %(message)s'))
        logger.addHandler(console_hdlr)
        logger.setLevel(logging.INFO)
        __logger__ = logger
        return __logger__