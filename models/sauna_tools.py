#!/usr/bin/python3

import json
import subprocess
from types import SimpleNamespace

import requests

import logging
logger = logging.getLogger('sauna')


# hostname of the audio controller of bluetooth speakers for announce
controller = 'tracfone'
controller = 'tablet'
controller = 'thinkpad'
controller = 'phone'


def announce(temperature, elapsed_time):

    args = [
        '/usr/bin/ssh',
        f'{controller}',
        'bin/announce',
        f'{temperature}',
        f'{elapsed_time:02}'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    return p


def start_media_player():
    logger.info('start media player')
    args = [
        '/usr/bin/ssh',
        f'{controller}',
        'bin/start-media-player'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    return p


def stop_media_player():
    logger.info('stop media player')
    args = [
        '/usr/bin/ssh',
        f'{controller}',
        'bin/stop-media-player'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )
    return p


def turn_sauna_light_on():
    # logger.info('turn sauna light on')
    args = [
        '/home/the-yarnist/bin/rgba-poke',
        'sauna-bulb-1',
        '255,0,0,255'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )
    return p


def turn_sauna_light_off():
    # logger.info('turn sauna light off')
    args = [
        '/home/the-yarnist/bin/rgba-poke',
        'sauna-bulb-1',
        '0,0,0,0'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )
    return p


def turn_sauna_heaters_on():
    # logger.info('turn sauna heater on')
    # 05-16-2023 sauna-heater-1 burned out, replaced with sauna-heater-3
    # kasa --host sauna-heater-3 --type plug on
    args = [
        '/home/the-yarnist/.local/bin/kasa',
        '--host',
        'sauna-heater-3',
        '--type',
        'plug',
        'on'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    args = [
        '/home/the-yarnist/.local/bin/kasa',
        '--host',
        'sauna-heater-2',
        '--type',
        'plug',
        'on'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    return p


def turn_sauna_heaters_off():
    # logger.info('turn sauna heaters off')
    # kasa --host sauna-heater-3 --type plug off
    args = [
        '/home/the-yarnist/.local/bin/kasa',
        '--host',
        'sauna-heater-3',
        '--type',
        'plug',
        'off'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    args = [
        '/home/the-yarnist/.local/bin/kasa',
        '--host',
        'sauna-heater-2',
        '--type',
        'plug',
        'off'
    ]
    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    return p


def get_sauna_temperature():

    ip = '192.168.1.154'     # sauna-sensor-1 ds18b20-sensor-1

    readings = []

    uri = 'http://' + ip + '/cm?cmnd=status%2010'
    r = requests.get(uri)
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(r.text, object_hook=lambda d: SimpleNamespace(**d))

    unit = response.StatusSNS.TempUnit

    if unit == 'F':
        temperature_f = response.StatusSNS.DS18B20.Temperature
        temperature_c = (temperature_f - 32) / 1.8
        pass
    elif unit == 'C':
        temperature_c = response.StatusSNS.DS18B20.Temperature
        temperature_f = (temperature_c * 9/5) + 32
    else:
        text = 'Error: unknown unit=' + unit
        return text

    temperature_c = round(temperature_c, 2)
    temperature_f = round(temperature_f, 2)

    readings.append({
        "temperature_c": temperature_c,
        "temperature_f": temperature_f
    })

    temperature_c = "{0:.2f}".format(temperature_c) + 'C'
    temperature_f = "{0:.2f}".format(temperature_f) + 'F'

    # sensor_reading = ' log-sensor: [DS18B20] temperature='
    # sensor_reading += temperature_c + ' / ' + temperature_f
    # logging.info(sensor_reading)

    text = json.dumps(readings)
    return text


def start_aux_fan():
    logger.info("start auxillary fan (room-fan-1)")
    args = [
        '/home/the-yarnist/.local/bin/kasa',
        '--host',
        'room-fan-1',
        '--type'
        'plug',
        'on'
    ]

    p = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )

    return p
