#  Copyright 2008-2013 Nokia Siemens Networks Oyj
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

from __future__ import with_statement

import sys
import os
import subprocess
import time
import signal as signal_module

from robot.utils import (ConnectionCache, abspath, encode_to_system,
                         decode_from_system, get_env_vars, secs_to_timestr,
                         timestr_to_secs)
from robot.version import get_version
from robot.api import logger


class Process(object):
    """Robot Framework test library for running processes.

    This library utilizes Python's
    [http://docs.python.org/2/library/subprocess.html|subprocess]
    module and its
    [http://docs.python.org/2/library/subprocess.html#subprocess.Popen|Popen]
    class.

    The library has following main usages:

    - Running processes in system and waiting for their completion using
      `Run Process` keyword.
    - Starting processes on background using `Start Process`.
    - Waiting started process to complete using `Wait For Process` or
      stopping them with `Terminate Process` or `Terminate All Processes`.

    This library is new in Robot Framework 2.8.

    == Table of contents ==

    - `Specifying command and arguments`
    - `Process configuration`
    - `Active process`
    - `Result object`
    - `Boolean arguments`
    - `Using with OperatingSystem library`
    - `Example`
    - `Shortcuts`
    - `Keywords`

    = Specifying command and arguments =

    Both `Run Process` and `Start Process` accept the command to execute
    and all arguments passed to it as separate arguments. This is convenient
    to use and also allows these keywords to automatically escape possible
    spaces and other special characters in the command or arguments.

    When `running processes in shell`, it is also possible to give the
    whole command to execute as a single string. The command can then
    contain multiple commands, for example, connected with pipes. When
    using this approach the caller is responsible on escaping.

    Examples:
    | `Run Process` | ${progdir}${/}prog.py        | first arg | second         |
    | `Run Process` | script1.sh arg && script2.sh | shell=yes | cwd=${progdir} |

    = Process configuration =

    `Run Process` and `Start Process` keywords can be configured using
    optional `**configuration` keyword arguments. Configuration arguments
    must be given after other arguments passed to these keywords and must
    use syntax like `name=value`. Available configuration arguments are
    listed below and discussed further in sections afterwards.

    |  = Name =  |                  = Explanation =                      |
    | shell      | Specifies whether to run the command in shell or not  |
    | cwd        | Specifies the working directory.                      |
    | env        | Specifies environment variables given to the process. |
    | env:<name> | Overrides the named environment variable(s) only.     |
    | stdout     | Path of a file where to write standard output.        |
    | stderr     | Path of a file where to write standard error.         |
    | alias      | Alias given to the process.                           |

    == Running processes in shell ==

    The `shell` argument specifies whether to run the process in a shell or
    not. By default shell is not used, which means that shell specific
    commands, like `copy` and `dir` on Windows, are not available.

    Giving the `shell` argument any non-false value, such as `shell=True`,
    changes the program to be executed in a shell. It allows using the shell
    capabilities, but can also make the process invocation operating system
    dependent.

    When using a shell it is possible to give the whole command to execute
    as a single string. See `Specifying command and arguments` section for
    examples and more details in general.

    == Current working directory ==

    By default the child process will be executed in the same directory
    as the parent process, the process running tests, is executed. This
    can be changed by giving an alternative location using the `cwd` argument.
    Forward slashes in the given path are automatically converted to
    backslashes on Windows.

    `Standard output and error streams`, when redirected to files,
    are also relative to the current working directory possibly set using
    the `cwd` argument.

    Example:
    | `Run Process` | prog.exe | cwd=${ROOT}/directory | stdout=stdout.txt |

    == Environment variables ==

    By default the child process will get a copy of the parent process's
    environment variables. The `env` argument can be used to give the
    child a custom environment as a Python dictionary. If there is a need
    to specify only certain environment variable, it is possible to use the
    `env:<name>=<value>` format to set or override only that named variables.
    It is also possible to use these two approaches together.

    Examples:
    | `Run Process` | program | env=${environ} |
    | `Run Process` | program | env:http_proxy=10.144.1.10:8080 | env:PATH=%{PATH}${:}${PROGDIR} |
    | `Run Process` | program | env=${environ} | env:EXTRA=value |

    == Standard output and error streams ==

    By default processes are run so that their standard output and standard
    error streams are kept in the memory. This works fine normally,
    but if there is a lot of output, the output buffers may get full and
    the program can hang.

    To avoid output buffers getting full, it is possible to use `stdout`
    and `stderr` arguments to specify files on the file system where to
    redirect the outputs. This can also be useful if other processes or
    other keywords need to read or manipulate the outputs somehow.

    Given `stdout` and `stderr` paths are relative to the `current working
    directory`. Forward slashes in the given paths are automatically converted
    to backslashes on Windows.

    As a special feature, it is possible to redirect the standard error to
    the standard output by using `stderr=STDOUT`.

    Regardless are outputs redirected to files or not, they are accessible
    through the `result object` returned when the process ends.

    Examples:
    | ${result} = | `Run Process` | program | stdout=${TEMPDIR}/stdout.txt | stderr=${TEMPDIR}/stderr.txt |
    | `Log Many`  | stdout: ${result.stdout} | stderr: ${result.stderr} |
    | ${result} = | `Run Process` | program | stderr=STDOUT |
    | `Log`       | all output: ${result.stdout} |

    Note that the created output files are not automatically removed after
    the test run. The user is responsible to remove them if needed.

    == Alias ==

    A custom name given to the process that can be used when selecting the
    `active process`.

    Examples:
    | `Start Process` | program | alias=example |
    | `Run Process`   | python  | -c | print 'hello' | alias=hello |

    = Active process =

    The test library keeps record which of the started processes is currently
    active. By default it is latest process started with `Start Process`,
    but `Switch Process` can be used to select a different one. Using
    `Run Process` does not affect the active process.

    The keywords that operate on started processes will use the active process
    by default, but it is possible to explicitly select a different process
    using the `handle` argument. The handle can be the identifier returned by
    `Start Process` or an `alias` explicitly given to `Start Process` or
    `Run Process`.

    = Result object =

    `Run Process`, `Wait For Process` and `Terminate Process` keywords return a
    result object that contains information about the process execution as its
    attributes. The same result object, or some of its attributes, can also
    be get using `Get Process Result` keyword. Attributes available in the
    object are documented in the table below.

    | = Attribute = |             = Explanation =               |
    | rc            | Return code of the process as an integer. |
    | stdout        | Contents of the standard output stream.   |
    | stderr        | Contents of the standard error stream.    |
    | stdout_path   | Path where stdout was redirected or `None` if not redirected. |
    | stderr_path   | Path where stderr was redirected or `None` if not redirected. |

    Example:
    | ${result} =            | `Run Process`         | program               |
    | `Should Be Equal As Integers` | ${result.rc}   | 0                     |
    | `Should Match`         | ${result.stdout}      | Some t?xt*            |
    | `Should Be Empty`      | ${result.stderr}      |                       |
    | ${stdout} =            | `Get File`            | ${result.stdout_path} |
    | `Should Be Equal`      | ${stdout}             | ${result.stdout}      |
    | `File Should Be Empty` | ${result.stderr_path} |                       |

    = Boolean arguments =

    Some keywords accept arguments that are handled as Boolean values.
    If such an argument is given as a string, it is considered false if it
    is either empty or case-insensitively equal to `false`. Other strings
    are considered true regardless what they contain, and other argument
    types are tested using same
    [http://docs.python.org/2/library/stdtypes.html#truth-value-testing|rules
    as in Python].

    True examples:
    | `Terminate Process` | kill=True     | # Strings are generally true.    |
    | `Terminate Process` | kill=yes      | # Same as above.                 |
    | `Terminate Process` | kill=${TRUE}  | # Python `True` is true.         |
    | `Terminate Process` | kill=${42}    | # Numbers other than 0 are true. |

    False examples:
    | `Terminate Process` | kill=False    | # String `False` is false.       |
    | `Terminate Process` | kill=${EMPTY} | # Empty string is false.         |
    | `Terminate Process` | kill=${FALSE} | # Python `False` is false.       |
    | `Terminate Process` | kill=${0}     | # Number 0 is false.             |

    Note that prior to Robot Framework 2.8 all non-empty strings, including
    `false`, were considered true.

    = Using with OperatingSystem library =

    The OperatingSystem library also contains keywords for running processes.
    They are not as flexible as the keywords provided by this library, and
    thus not recommended to be used anymore. They may eventually even be
    deprecated.

    There is a name collision because both of these libraries have
    `Start Process` and `Switch Process` keywords. This is handled so that
    if both libraries are imported, the keywords in the Process library are
    used by default. If there is a need to use the OperatingSystem variants,
    it is possible to use `OperatingSystem.Start Process` syntax or use
    the `BuiltIn` keyword `Set Library Search Order` to change the priority.

    Other keywords in the OperatingSystem library can be used freely with
    keywords in the Process library.

    = Example =

    | ***** Settings *****
    | Library    Process
    | Suite Teardown    `Terminate All Processes`    kill=True
    |
    | ***** Test Cases *****
    | Example
    |     `Start Process`    program    arg1   arg2    alias=First
    |     ${handle} =    `Start Process`    command.sh arg | command2.sh   shell=True    cwd=/path
    |     ${result} =    `Run Process`    ${CURDIR}/script.py
    |     `Should Not Contain`    ${result.stdout}    FAIL
    |     `Terminate Process`    ${handle}
    |     ${result} =    `Wait For Process`    First
    |     `Should Be Equal As Integers`   ${result.rc}    0
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    TERMINATE_TIMEOUT = 30
    KILL_TIMEOUT = 10

    def __init__(self):
        self._processes = ConnectionCache('No active process.')
        self._results = {}

    def run_process(self, command, *arguments, **configuration):
        """Runs a process and waits for it to complete.

        See `Specifying command and arguments` and `Process configuration`
        for more information about the arguments.

        Returns a `result object` containing information about the execution.

        This command does not change the `active process`.
        """
        current = self._processes.current
        try:
            handle = self.start_process(command, *arguments, **configuration)
            return self.wait_for_process(handle)
        finally:
            self._processes.current = current

    def start_process(self, command, *arguments, **configuration):
        """Starts a new process on background.

        See `Specifying command and arguments` and `Process configuration`
        for more information about the arguments.

        Makes the started process new `active process`. Returns an identifier
        that can be used as a handle to active the started process if needed.
        """
        config = ProcessConfig(**configuration)
        executable_command = self._cmd(arguments, command, config.shell)
        logger.info('Starting process:\n%s' % executable_command)
        logger.debug('Process configuration:\n%s' % config)
        process = subprocess.Popen(executable_command,
                                   stdout=config.stdout_stream,
                                   stderr=config.stderr_stream,
                                   stdin=subprocess.PIPE,
                                   shell=config.shell,
                                   cwd=config.cwd,
                                   env=config.env,
                                   universal_newlines=True)
        self._results[process] = ExecutionResult(process,
                                                 config.stdout_stream,
                                                 config.stderr_stream)
        return self._processes.register(process, alias=config.alias)

    def _cmd(self, args, command, use_shell):
        command = [encode_to_system(item) for item in [command] + list(args)]
        if not use_shell:
            return command
        if args:
            return subprocess.list2cmdline(command)
        return command[0]

    def is_process_running(self, handle=None):
        """Checks is the process running or not.

        If `handle` is not given, uses the current `active process`.

        Returns `True` if the process is still running and `False` otherwise.
        """
        return self._processes[handle].poll() is None

    def process_should_be_running(self, handle=None,
                                  error_message='Process is not running.'):
        """Verifies that the process is running.

        If `handle` is not given, uses the current `active process`.

        Fails if the process has stopped.
        """
        if not self.is_process_running(handle):
            raise AssertionError(error_message)

    def process_should_be_stopped(self, handle=None,
                                  error_message='Process is running.'):
        """Verifies that the process is not running.

        If `handle` is not given, uses the current `active process`.

        Fails if the process is still running.
        """
        if self.is_process_running(handle):
            raise AssertionError(error_message)

    def wait_for_process(self, handle=None, timeout=None, on_timeout='continue'):
        """Waits for the process to complete or to reach the given timeout.

        The process to wait for must have been started earlier with
        `Start Process`. If `handle` is not given, uses the current
        `active process`.

        `timeout` defines the maximum time to wait for the process. It is
        interpreted according to Robot Framework User Guide Appendix
        `Time Format`, for example, '42', '42 s', or '1 minute 30 seconds'.

        `on_timeout` defines what to do if the timeout occurs. Possible values
        and corresponding actions are explained in the table below. Notice
        that reaching the timeout never fails the test.

        |  = Value =  |               = Action =               |
        | `continue`  | The process is left running (default). |
        | `terminate` | The process is gracefully terminated.  |
        | `kill`      | The process is forcefully stopped.     |

        See `Terminate Process` keyword for more details how processes are
        terminated and killed.

        If the process ends before the timeout or it is terminated or killed,
        this keyword returns a `result object` containing information about
        the execution. If the process is left running, Python `None` is
        returned instead.

        Examples:
        | # Process ends cleanly      |                  |                  |
        | ${result} =                 | Wait For Process | example          |
        | Process Should Be Stopped   | example          |                  |
        | Should Be Equal As Integers | ${result.rc}     | 0                |
        | # Process does not end      |                  |                  |
        | ${result} =                 | Wait For Process | timeout=42 secs  |
        | Process Should Be Running   |                  |                  |
        | Should Be Equal             | ${result}        | ${NONE}          |
        | # Kill non-ending process   |                  |                  |
        | ${result} =                 | Wait For Process | timeout=1min 30s | on_timeout=kill |
        | Process Should Be Stopped   |                  |                  |
        | Should Be Equal As Integers | ${result.rc}     | -9               |

        `timeout` and `on_timeout` are new in Robot Framework 2.8.2.
        """
        process = self._processes[handle]
        result = self._results[process]
        logger.info('Waiting for process to complete.')
        if timeout:
            timeout = timestr_to_secs(timeout)
            if not self._process_is_stopped(process, timeout):
                logger.info('Process did not complete in %s.'
                            % secs_to_timestr(timeout))
                return self._manage_process_timeout(handle, on_timeout.lower())
        result.rc = process.wait() or 0
        logger.info('Process completed.')
        return result

    def _manage_process_timeout(self, handle, on_timeout):
        if on_timeout == 'terminate':
            return self.terminate_process(handle)
        elif on_timeout == 'kill':
            return self.terminate_process(handle, kill=True)
        else:
            logger.info('Leaving process intact.')
            return None

    def terminate_process(self, handle=None, kill=False):
        """Stops the process gracefully or forcefully.

        If `handle` is not given, uses the current `active process`.

        Waits for the process to stop after terminating it. Returns
        a `result object` containing information about the execution
        similarly as `Wait For Process`.

        On Unix-like machines, by default, first tries to terminate the process
        gracefully, but forcefully kills it if it does not stop in 30 seconds.
        Kills the process immediately if the `kill` argument is given any value
        considered true. See `Boolean arguments` section for more details about
        true and false values.

        Termination is done using `TERM (15)` signal and killing using
        `KILL (9)`. Use `Send Signal To Process` instead if you just want to
        send either of these signals without waiting for the process to stop.

        On Windows the Win32 API function `TerminateProcess()` is used directly
        to stop the process. Using the `kill` argument has no special effect.

        | ${result} =                 | Terminate Process |           |
        | Should Be Equal As Integers | ${result.rc}      | -15       |
        | Terminate Process           | myproc            | kill=true |

        *NOTE:* Stopping processes requires the
        [http://docs.python.org/2/library/subprocess.html|subprocess]
        module to have working `terminate` and `kill` functions. They were
        added in Python 2.6 and are thus missing from earlier versions.
        Unfortunately at least beta releases of Jython 2.7
        [http://bugs.jython.org/issue1898|do not seem to support them either].

        Automatically killing the process if termination fails as well as
        returning the result object are new features in Robot Framework 2.8.2.
        """
        process = self._processes[handle]
        result = self._results[process]
        if not hasattr(process, 'terminate'):
            raise RuntimeError('Terminating processes is not supported '
                               'by this Python version.')
        terminator = self._kill if is_true(kill) else self._terminate
        try:
            terminator(process)
        except OSError:
            if not self._process_is_stopped(process, self.KILL_TIMEOUT):
                raise
            logger.debug('Ignored OSError because process was stopped.')
        result.rc = process.wait() or 0
        return result

    def _kill(self, process):
        logger.info('Forcefully killing process.')
        process.kill()
        if not self._process_is_stopped(process, self.KILL_TIMEOUT):
            raise RuntimeError('Failed to kill process.')

    def _terminate(self, process):
        logger.info('Gracefully terminating process.')
        process.terminate()
        if not self._process_is_stopped(process, self.TERMINATE_TIMEOUT):
            logger.info('Graceful termination failed.')
            self._kill(process)

    def terminate_all_processes(self, kill=False):
        """Terminates all still running processes started by this library.

        This keyword can be used in suite teardown or elsewhere to make
        sure that all processes are stopped,

        By default tries to terminate processes gracefully, but can be
        configured to forcefully kill them immediately. See `Terminate Process`
        that this keyword uses internally for more details.
        """
        for handle in range(1, len(self._processes) + 1):
            if self.is_process_running(handle):
                self.terminate_process(handle, kill=kill)
        self.__init__()

    def send_signal_to_process(self, signal, handle=None):
        """Sends the given `signal` to the specified process.

        If `handle` is not given, uses the current `active process`.

        Signal can be specified either as an integer, or anything that can
        be converted to an integer, or as a name. In the latter case it is
        possible to give the name both with or without a `SIG` prefix,
        but names are case-sensitive. For example, all the examples below
        send signal `INT (2)`:

        | Send Signal To Process | 2      |        | # Send to active process |
        | Send Signal To Process | INT    |        |                          |
        | Send Signal To Process | SIGINT | myproc | # Send to named process  |

        What signals are supported depends on the system. For a list of
        existing signals on your system, see the Unix man pages related to
        signal handling (typically `man signal` or `man 7 signal`).

        If you are stopping a process, it is often easier and safer to use
        `Terminate Process` instead.

        *NOTE:* Sending signals requires the
        [http://docs.python.org/2/library/subprocess.html|subprocess]
        module to have working `send_signal` function. It was added
        in Python 2.6 and are thus missing from earlier versions.
        How well it will work with forthcoming Jython 2.7 is unknown.

        New in Robot Framework 2.8.2.
        """
        if os.sep == '\\':
            raise RuntimeError('This keyword does not work on Windows.')
        process = self._processes[handle]
        if not hasattr(process, 'send_signal'):
            raise RuntimeError('Sending signals is not supported '
                               'by this Python version.')
        process.send_signal(self._get_signal_number(signal))

    def _get_signal_number(self, int_or_name):
        try:
            return int(int_or_name)
        except ValueError:
            return self._convert_signal_name_to_number(int_or_name)

    def _convert_signal_name_to_number(self, name):
        try:
            return getattr(signal_module,
                           name if name.startswith('SIG') else 'SIG' + name)
        except AttributeError:
            raise RuntimeError("Unsupported signal '%s'." % name)

    def get_process_id(self, handle=None):
        """Returns the process ID (pid) of the process.

        If `handle` is not given, uses the current `active process`.

        Returns the pid assigned by the operating system as an integer.
        Note that with Jython, at least with the 2.5 version, the returned
        pid seems to always be `None`.

        The pid is not the same as the identifier returned by
        `Start Process` that is used internally by this library.
        """
        return self._processes[handle].pid

    def get_process_object(self, handle=None):
        """Return the underlying `subprocess.Popen`  object.

        If `handle` is not given, uses the current `active process`.
        """
        return self._processes[handle]

    def get_process_result(self, handle=None, rc=False, stdout=False,
                           stderr=False, stdout_path=False, stderr_path=False):
        """Returns the specified `result object` or some of its attributes.

        The given `handle` specifies the process whose results should be
        returned. If no `handle` is given, results of the current `active
        process` are returned. In either case, the process must have been
        finishes before this keyword can be used. In practice this means
        that processes started with `Start Process` must be finished either
        with `Wait For Process` or `Terminate Process` before using this
        keyword.

        If no other arguments than the optional `handle` are given, a whole
        `result object` is returned. If one or more of the other arguments
        are given any true value, only the specified attributes of the
        `result object` are returned. These attributes are always returned
        in the same order as arguments are specified in the keyword signature.
        See `Boolean arguments` section for more details about true and false
        values.

        Examples:
        | Run Process           | python             | -c            | print 'Hello, world!' | alias=myproc |
        | # Get result object   |                    |               |
        | ${result} =           | Get Process Result | myproc        |
        | Should Be Equal       | ${result.rc}       | ${0}          |
        | Should Be Equal       | ${result.stdout}   | Hello, world! |
        | Should Be Empty       | ${result.stderr}   |               |
        | # Get one attribute   |                    |               |
        | ${stdout} =           | Get Process Result | myproc        | stdout=true |
        | Should Be Equal       | ${stdout}          | Hello, world! |
        | # Multiple attributes |                    |               |
        | ${stdout}             | ${stderr} =        | Get Process Result |  myproc | stdout=yes | stderr=yes |
        | Should Be Equal       | ${stdout}          | Hello, world! |
        | Should Be Empty       | ${stderr}          |               |

        Although getting results of a previously executed process can be handy
        in general, the main use case for this keyword is returning results
        over the remote library interface. The remote interface does not
        support returning the whole result object, but individual attributes
        can be returned without problems.

        New in Robot Framework 2.8.2.
        """
        result = self._results[self._processes[handle]]
        if result.rc is None:
            raise RuntimeError('Getting results of unfinished processes '
                               'is not supported.')
        attributes = self._get_result_attributes(result, rc, stdout, stderr,
                                                 stdout_path, stderr_path)
        if not attributes:
            return result
        elif len(attributes) == 1:
            return attributes[0]
        return attributes

    def _get_result_attributes(self, result, *includes):
        attributes = (result.rc, result.stdout, result.stderr,
                      result.stdout_path, result.stderr_path)
        includes = (is_true(incl) for incl in includes)
        return tuple(attr for attr, incl in zip(attributes, includes) if incl)

    def switch_process(self, handle):
        """Makes the specified process the current `active process`.

        The handle can be an identifier returned by `Start Process` or
        the `alias` given to it explicitly.

        Example:
        | Start Process  | prog1    | alias=process1 |
        | Start Process  | prog2    | alias=process2 |
        | # currently active process is process2 |
        | Switch Process | process1 |
        | # now active process is process1 |
        """
        self._processes.switch(handle)

    def _process_is_stopped(self, process, timeout):
        max_time = time.time() + timeout
        while time.time() <= max_time:
            if process.poll() is not None:
                return True
            time.sleep(0.1)
        return False


class ExecutionResult(object):

    def __init__(self, process, stdout, stderr, rc=None):
        self._process = process
        self.stdout_path = self._get_path(stdout)
        self.stderr_path = self._get_path(stderr)
        self.rc = rc
        self._stdout = None
        self._stderr = None

    def _get_path(self, stream):
        if stream in (subprocess.PIPE, subprocess.STDOUT):
            return None
        return stream.name

    @property
    def stdout(self):
        if self._stdout is None:
            self._stdout = self._read_stream(self.stdout_path,
                                             self._process.stdout)
        return self._stdout

    @property
    def stderr(self):
        if self._stderr is None:
            self._stderr = self._read_stream(self.stderr_path,
                                             self._process.stderr)
        return self._stderr

    def _read_stream(self, stream_path, stream):
        if stream_path:
            stream = open(stream_path, 'r')
        try:
            return self._format_output(stream.read() if stream else '')
        finally:
            if stream_path:
                stream.close()

    def _format_output(self, output):
        if output.endswith('\n'):
            output = output[:-1]
        return decode_from_system(output)

    def __str__(self):
        return '<result object with rc %d>' % self.rc


class ProcessConfig(object):

    def __init__(self, cwd=None, shell=False, stdout=None, stderr=None,
                 alias=None, env=None, **rest):
        self.cwd = self._get_cwd(cwd)
        self.stdout_stream = self._new_stream(stdout)
        self.stderr_stream = self._get_stderr(stderr, stdout)
        self.shell = is_true(shell)
        self.alias = alias
        self.env = self._construct_env(env, rest)

    def _get_cwd(self, cwd):
        if cwd:
            return cwd.replace('/', os.sep)
        return abspath('.')

    def _new_stream(self, name):
        if name:
            name = name.replace('/', os.sep)
            return open(os.path.join(self.cwd, name), 'w')
        return subprocess.PIPE

    def _get_stderr(self, stderr, stdout):
        if stderr:
            if stderr == 'STDOUT' or stderr == stdout:
                if self.stdout_stream == subprocess.PIPE:
                    return subprocess.STDOUT
                return self.stdout_stream
        return self._new_stream(stderr)

    def _construct_env(self, env, rest):
        for key in rest:
            if not key.startswith('env:'):
                raise RuntimeError("'%s' is not supported by this keyword." % key)
            if env is None:
                env = get_env_vars(upper=False)
            env[key[4:]] = rest[key]
        if env:
            env = dict((encode_to_system(key), encode_to_system(env[key]))
                       for key in env)
        return env

    def __str__(self):
        return encode_to_system("""\
cwd = %s
stdout_stream = %s
stderr_stream = %s
shell = %r
alias = %s
env = %r""" % (self.cwd, self.stdout_stream, self.stderr_stream,
               self.shell, self.alias, self.env))


def is_true(argument):
    if isinstance(argument, basestring) and argument.upper() == 'FALSE':
        return False
    return bool(argument)
