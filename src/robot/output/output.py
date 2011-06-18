#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import re

from robot.common.statistics import Statistics
from robot import utils
import robot

from loggerhelper import AbstractLogger, Message, LEVELS
from logger import LOGGER
from xmllogger import XmlLogger
from listeners import Listeners
from debugfile import DebugFile


class Output(AbstractLogger):

    def __init__(self, settings):
        AbstractLogger.__init__(self)
        self._xmllogger = XmlLogger(settings['Output'], settings['LogLevel'])
        self._register_loggers(settings['Listeners'], settings['DebugFile'])
        self._settings = settings
        robot.output.OUTPUT = self

    def _register_loggers(self, listeners, debugfile):
        LOGGER.register_context_changing_logger(self._xmllogger)
        for logger in Listeners(listeners), DebugFile(debugfile):
            if logger: LOGGER.register_logger(logger)
        LOGGER.disable_message_cache()

    def close(self, suite):
        stats = Statistics(suite, self._settings['SuiteStatLevel'],
                           self._settings['TagStatInclude'],
                           self._settings['TagStatExclude'],
                           self._settings['TagStatCombine'],
                           self._settings['TagDoc'],
                           self._settings['TagStatLink'])
        stats.serialize(self._xmllogger)
        self._xmllogger.close()
        LOGGER.unregister_logger(self._xmllogger)
        LOGGER.output_file('Output', self._settings['Output'])

    def start_suite(self, suite):
        LOGGER.start_suite(suite)

    def end_suite(self, suite):
        LOGGER.end_suite(suite)

    def start_test(self, test):
        LOGGER.start_test(test)

    def end_test(self, test):
        LOGGER.end_test(test)

    def start_keyword(self, kw):
        LOGGER.start_keyword(kw)

    def end_keyword(self, kw):
        LOGGER.end_keyword(kw)

    def log_output(self, output):
        """Splits given output to levels and messages and logs them"""
        for msg in _OutputSplitter(output):
            self.message(msg)

    def message(self, msg):
        LOGGER.log_message(msg)

    def set_log_level(self, level):
        return self._xmllogger.set_log_level(level)


class _OutputSplitter:
    _split_from_levels = re.compile('^(?:\*'
                                    '(%s|HTML)'          # Level
                                    '(:\d+(?:\.\d+)?)?'  # Optional timestamp
                                    '\*)' % '|'.join(LEVELS), re.MULTILINE)

    def __init__(self, output):
        self._messages = list(self._get_messages(output.strip()))

    def _get_messages(self, output):
        for level, timestamp, msg in self._split_output(output):
            if timestamp:
                timestamp = self._format_timestamp(timestamp[1:])
            yield Message(msg.strip(), level, timestamp=timestamp)

    def _split_output(self, output):
        tokens = self._split_from_levels.split(output)
        tokens = self._add_initial_level_and_time_if_needed(tokens)
        for i in xrange(0, len(tokens), 3):
            yield tokens[i:i+3]

    def _add_initial_level_and_time_if_needed(self, tokens):
        if self._output_started_with_level(tokens):
            return tokens[1:]
        return ['INFO', None] + tokens

    def _output_started_with_level(self, tokens):
        return tokens[0] == ''

    def _format_timestamp(self, millis):
        return utils.format_time(float(millis)/1000, millissep='.')

    def __iter__(self):
        return iter(self._messages)
