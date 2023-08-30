#!/usr/bin/python3

import asyncio
from datetime import datetime, timedelta
import json
import math
import os
import platform
import sys
from select import select
import signal
import subprocess

import logging


from models.sauna_tools import (
    announce,
    start_aux_fan,
    start_media_player,
    stop_media_player,
    turn_sauna_light_on,
    turn_sauna_light_off,
    turn_sauna_heaters_on,
    turn_sauna_heaters_off,
    get_sauna_temperature

    )

logger = logging.getLogger('sauna')


class SaunaSession:

    temperature_c = 0
    previous_temperature_c = 0
    temperature_c_delta = 0

    temperature_f = 0
    previous_temperature_f = 0
    temperature_f_delta = 0

    lower_bound = 110
    restart_trigger = 118  # 115
    upper_bound = 120  # 118

    elapsed = None
    elapsed_minutes = None

    user_in_sauna = False

    heaters = False

    lights = ""

    brightness = 255

    action = ""

    reason = ""

    shutdown = False

    # in minutes, after this many minutes signal that the session is overe
    normal_session_length = 15
    normal_session_length = 20
#    normal_session_length = 17

    # in minutes, after this many minutes force shtudown the sauna
    maximum_session_length = 20

    # in seconds, this is warm-up time + session-time and is the maximum
    # length of time the sauna can be on
    # (basically we don't want to run out of water and burn something)
    maximum_run_length = (50 * 60)

    system_session_start = datetime.now()
    user_session_start = None       # starts when the user enters the session

    # in seconds
    # how often the keyboard handler will check for keypresses
    keyboard_polling_interval = 1

    # in seconds
    # how often to poll sensors and update the sauna
    sensor_polling_interval = 5
    sensor_polling_interval = 10

    # in seconds
    # how often to log the sauna state to file/screen
    logging_interval = 20
    logging_interval = 10

    # in seconds,
    # how long to wait until the next iteration of the announce_handler
    announce_wait = 60

    # signals the sauna has reached operating temperature and is ready
    # for someone to enter
    is_ready = False

    # flag to determine if the normal_session_length timeout
    # has expired/been signaled
    normal_session_exceeded = False

    # flag to determine if the user has exited the sauna
    user_exited_sauna = False

    # in minutes, how long before the system will attempt to
    # auto-detect user-exiting events
    can_exit_threshold = 10  # bumped from 5 to 10

    def get_state(self):

        text = get_sauna_temperature()

        try:
            temperatures = json.loads(text)[0]
        except Exception as err:
            print(f"Unexpected {err=}")
            msg = (f"unexpected {err=}:"
                   f"text={text}")
            logger.info(msg)
            return False

        if self.previous_temperature_c == 0:
            self.previous_temperature_c = temperatures["temperature_c"]
            self.previous_temperature_f = temperatures["temperature_f"]
        else:
            self.previous_temperature_c = self.temperature_c
            self.previous_temperature_f = self.temperature_f

        self.temperature_c = temperatures["temperature_c"]
        self.temperature_f = temperatures["temperature_f"]

        self.temperature_c_delta = (self.previous_temperature_c -
                                    self.temperature_c)

#        self.temperature_f_delta = (self.previous_temperature_f -
#                                    self.temperature_f)

        self.temperature_f_delta = self.temperature_f
        self.temperature_f_delta -= self.previous_temperature_f

    def update_sauna(self):

        if self.heaters:
            turn_sauna_heaters_on()
        else:
            turn_sauna_heaters_off()

        turn_sauna_light_on()
        #
        # /api/sauna/lights/color/{self.lights}/{self.brightness}
        #

        return True

    def apply_state(self):

        if not self.is_ready:
            if self.temperature_f > self.lower_bound:
                self.is_ready = self.acknowledge_sauna_ready()
                if not self.is_ready:
                    self.shutdown = True
                    return True
                # get the temperature twice becuase the user might have
                # waited 4+ minutes before acknowledging# the sauna was ready.
                # in that amount of time the temperature (and its delta) can
                # change alot and trigger false user_in_sauna readings
                self.get_state()
                self.get_state()

        if (self.is_ready and not self.user_in_sauna and
                self.temperature_f_delta <= -0.5):
            self.fmt_log_msg()
            msg = (f'user has entered the sauna: '
                   f'𝛥={self.temperature_c_delta:.3}C '
                   f'{self.temperature_f_delta:.3}F')
            logger.info(msg)
            start_media_player()
            self.user_in_sauna = True
            self.user_session_start = datetime.now()

        if self.temperature_f < self.lower_bound:
            self.lights = "blue"
            self.lights = 'cool-white'
            self.lights = "red"
            self.brightness = 64
            self.heaters = True
        elif self.temperature_f > self.upper_bound:
            self.lights = "red"
            self.lights = 'warm-white'
            self.lights = "red"
            self.brightness = 128
            self.heaters = False
        else:
            self.lights = "bright-white"
            self.lights = "red"
            self.brightness = 255

        if self.temperature_f < self.restart_trigger:
            self.heaters = True

        if self.user_in_sauna:
            current = datetime.now()
            delta_t = (current - self.user_session_start)
            self.elapsed = int(delta_t.total_seconds())
            self.elapsed_minutes = int(self.elapsed / 60)
        else:
            self.elapsed = 0
            self.elapsed_minutes = 0

        # signal the user to get out if the normal_session_length
        # (default:15 minutes) has been exceeded
        if self.elapsed_minutes >= self.normal_session_length:
            if not self.normal_session_exceeded:
                msg = (f'signal normal user session length '
                       f'({self.normal_session_length} minutes) exceeded')
                logger.info(msg)
                self.normal_session_exceeded = True
            self.lights = "black-light"
            self.brightness = 255
            self.heaters = False

        # in general, n=session.can_exit_threshold (default: 5 minutes) after
        # entering the sauna if the temperature goes below lower_bound then
        # the user has opened the door/exited so shut the sauna down.
        if (
            self.elapsed_minutes >= self.can_exit_threshold and
            self.temperature_f < self.lower_bound
        ):
            msg = (f'user has exited the sauna: '
                   f'temperature={self.temperature_f}ºF < '
                   f'{self.lower_bound}F')
            logger.info(msg)

            self.user_in_sauna = False
            self.user_exited_sauna = True
            self.shutdown = True

            return True

        # for safety, if the maximum_session_length expires, shutdown the sauna
        if self.elapsed_minutes >= self.maximum_session_length:
            msg = (f'safety theshold ({self.maximum_session_length} minutes) '
                   f'exceeded.  elapsed-time={self.elapsed_minutes} minutes.')
            logger.info(msg)

            self.shutdown = True
            return True

        self.update_sauna()

    async def state_handler(self):
        while True:
            if self.shutdown:
                return

            self.get_state()
            self.apply_state()

            await asyncio.sleep(self.sensor_polling_interval)

    def fmt_log_msg(self):
        msg = f'temperature={self.temperature_f:<05}ºF'
        msg += f', lights={self.lights}/{self.brightness}'
        msg += ', +' if self.heaters else ', -'
        msg += 'heaters'
        msg += ', +' if self.user_in_sauna else ', -'
        msg += 'user'
        if self.user_in_sauna:
            msg += ', elapsed=' + str(self.elapsed_minutes)
        logger.info(msg)

    async def log_handler(self):
        while True:

            await asyncio.sleep(self.logging_interval)

            if self.shutdown:
                return True

            msg = f'temperature={self.temperature_f:.1f}ºF'
            msg += f', 𝛥={self.temperature_f_delta:+.1f}'
            msg += f', lights={self.lights}/{self.brightness}'
            msg += ', +' if self.heaters else ', -'
            msg += 'heaters'
            msg += ', +' if self.user_in_sauna else ', -'
            msg += 'user'
            if self.user_in_sauna:
                msg += ', elapsed=' + str(self.elapsed_minutes)
            logger.info(msg)

    async def shutdown_handler(self):
        while True:
            await asyncio.sleep(1)

            if self.shutdown:
                for task in asyncio.all_tasks():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        # print(f'{task.get_name():18} is cancelled now')
                        pass
                self.graceful_exit()
                return

    #
    # poll the keyboard every (n = session.keyboard_polling_interval) seconds,
    # if a key is pressed assume the user has left the sauna
    # and is signalling to shut everything down gracefully.
    #
    async def keyboard_handler(self):
        while True:
            if self.is_ready:
                timeout = 0
                rlist, wlist, xlist = select([sys.stdin], [], [], timeout)

                if rlist:
                    logger.info('user has left the sauna, exit gracefully')
                    self.shutdown = True
                    return
            await asyncio.sleep(self.keyboard_polling_interval)

    # send the user in the sauna temperature and time information
    async def announce_handler(self):
        intervals = [2, 4, 6, 8, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        while True:
            await asyncio.sleep(self.announce_wait)

            if self.shutdown:
                return True

            if self.user_in_sauna:

                delta_t = (datetime.now() - self.user_session_start)
                elapsed_seconds = int(delta_t.total_seconds())
                self.elapsed_minutes = math.trunc(elapsed_seconds / 60)

                n = self.elapsed_minutes + 1
                next_interval = self.user_session_start + timedelta(minutes=n)
                self.announce_wait = (next_interval -
                                      datetime.now()).total_seconds()

                if self.elapsed_minutes in intervals:
                    announce(self.temperature_f, self.elapsed_minutes)
                    logger.debug(f'announce: '
                                 f'temperature={self.temperature_f}ºF '
                                 f'elapsed={self.elapsed_minutes} minutes')
                    logger.debug(f'next announcement in: '
                                 f'{self.announce_wait:.2f} seconds')
#            else:
#                logger.debug(f'announce: nothing to do, '
#                             f'user_in_sauna={self.user_in_sauna}')

    def acknowledge_sauna_ready(self):

        wait_for_input_timeout = 5                  # minutes
        timeout = wait_for_input_timeout * 60       # seconds

        logger.info('sauna has reached operating temperature')
        logger.info(f'alerting user to enter the sauna '
                    f'(timeout in {wait_for_input_timeout} minutes)')

        self.lights = "green"
        self.brightness = 255
        self.update_sauna()

        # play an alarm that will interrupt youtube/vlc music...
        args = ['/usr/bin/cvlc',
                '-q',
                '/usr/share/sounds/Oxygen-Sys-App-Error-Serious-Very.ogg'
                ]
        p = subprocess.Popen(args,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             stdin=None)

        # wait for user input or timeout
        rlist, wlist, xlist = select([sys.stdin], [], [], timeout)

        os.kill(p.pid, signal.SIGTERM)

        if rlist:
            logger.info("user has acknowledged the sauna is ready")
            from termios import tcflush, TCIOFLUSH
            tcflush(sys.stdin, TCIOFLUSH)
        else:
            logger.info('timed out waiting for user to acknowledge '
                        'sauna is ready - shutting down...')
            return False

        return True

    def graceful_exit(self, force_fan=True):
        turn_sauna_light_off()
        logger.info('power off sauna lights')

        turn_sauna_heaters_off()
        logger.info('power off sauna heaters')

        stop_media_player()

        if force_fan:
            start_aux_fan()

    def __init__(self):
        # configure standard logging
        # appname = r'sauna'
        appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        homedir = os.environ.get('HOME')
        logfile = homedir + r'/.local/log/' + appname + '.log'
        logheader = " ".join([
                                platform.node(),
                                appname + '[' + str(os.getpid()) + ']:'
                            ])

        logheader = " ".join([appname + '[' + str(os.getpid()) + ']:'])

        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s %(message)s',
                                      datefmt='%b %d %H:%M:%S ' + logheader)
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

#        logging.basicConfig(
#            level=logging.INFO,
#            format="%(asctime)s [%(levelname)s] %(message)s",
#            handlers=[
#                logging.FileHandler("sauna.log"),
#                logging.StreamHandler()
#            ]
#        )

        # add the handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)

        logger.info('enjoy the sauna')
        logger.info('waiting for the sauna to reach operating temperature')
        logger.info(f'lower-bound={self.lower_bound} '
                    f'upper-bound={self.upper_bound} '
                    f'restart-trigger={self.restart_trigger}')
