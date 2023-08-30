#!/usr/bin/env python3

import asyncio
import logging
import os
import sys

from models.sauna_session import SaunaSession

logger = logging.getLogger('sauna')


async def main(session):
    asyncio.current_task().set_name("main-program")

    # push state information to the user in sauna
    asyncio.create_task(session.announce_handler(), name="announce-handler")

    # listen for keypress, signals the user has exited
    asyncio.create_task(session.keyboard_handler(), name="keyboard-handler")

    # log sauna state to logfile/screen
    asyncio.create_task(session.log_handler(), name="log-handler")

    # generic shutdown handler {exit gracefully}
    asyncio.create_task(session.shutdown_handler(), name="shutdown-handler")

    # get state, apply the state, act on the stdate, log the state
    asyncio.create_task(session.state_handler(), name="state-handler")

    #
    # wait for a maximum of {default:50} minutes then force exit
    #
    await asyncio.sleep(session.maximum_run_length)

    #
    # code beyond this point should ideally never run
    # {the user exits the sauna before the timeout above}
    #

    logger.info('*** catastrophic error ***')
    logger.info(f'maximum-run-length ({int(session.maximum_run_length / 60)} '
                f'minutes) exceeded')
    session.graceful_exit(force_fan=False)


try:
    os.system('stty -echo')
    session = SaunaSession()
    asyncio.run(main(session))
except KeyboardInterrupt:
    sys.stderr.write("\r")
    logger.info('ctrl-c interrupt: forced graceful shutdown')
    session.graceful_exit(force_fan=False)
except asyncio.CancelledError:
    # logging.info(asyncio.CancelledError)
    pass
finally:
    os.system('stty echo')

# TODO:
#   1) any suggestions?
#   2) use asyncio compatible requests library
#   3) sanity-check every n-seconds make sure can reach heaters+light
#      and their physical state matches the software's tracked state
#   4) update then verify new status when change heaters+lights
#
#   1) --meditate flag, uses the meditate playlist, turns off announcements,
#      set the session to 16 minutes
#   2) --announcement flag {yes/no}
#   3) log to a file, and make a GUI for the status. make a log parser to show
#      the current status
#   4) increase the granularity of the get-temperature task
#   5) create service that only comes up when the network interface is up
#   6) add +/- delta to logging
#   7) replace /api/sauna/sensors/temperature with direct call to the tasmota
#      sauna temperature
#   8) modify init so previous_temperature and temperature are assigned
#      current temperature in *init*
#   9) in apply state if not self.is_ready
#      {if the temperature < self.lower_bound RETURN}
#   1) Move sauna + sauna-session to their own project,
#      remove soard from the dependencies
#   2) move to profiles with lower/upper/trigger, announce, playlist,
#      heater-ips (or # heaters), intervals
#   3) remove aux-fan support
#   4) remove all 'red' lights, and 'blue' lights,
#      use cool-white, bright-white, and warm white for indicators
