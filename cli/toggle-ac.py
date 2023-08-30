#!/usr/bin/python3

import json
import time

import requests


def get_temperature():

    temperature_uri = 'http://192.168.1.156/cm?cmnd=status%2010'
    response = requests.get(temperature_uri)

    # BUGFIX: sometimes the nodemcu returns null values in the response string, so re-query
    # while temperature is None:
    while json.loads(response.text)['StatusSNS']['AM2301']['Temperature'] is None:
        time.sleep(5)
        response = requests.get(temperature_uri)
        print(response.text)
        print( 'temperature:', json.loads(response.text)['StatusSNS']['AM2301']['Temperature'] )

    temperature = float(json.loads(response.text)['StatusSNS']['AM2301']['Temperature'])

    return temperature


def toggle_ac():

    #payload = {'cmnd':'IRhvac {"Vendor":"WHIRLPOOL_AC", "Power":"On", "Mode":"Cool", "Temp":' + str(target_temperature) + ', "FanSpeed":"Max", "Light":"On", "SwingV":"On", "SwingH":"On"}'}
    payload = {'cmnd':'IRhvac {"Vendor":"WHIRLPOOL_AC", "Power":"On", "Mode":"Cool", "Temp":23, "FanSpeed":"Max", "Light":"On", "SwingV":"On", "SwingH":"On"}'}
    print(payload)

    url = 'http://192.168.1.137/cm'
    #url = 'http://httpbin.org/get'

    r = requests.get(url, params=payload)

    print(r)
    print(r.text)


def main():

    temperature = get_temperature()
    print( 'temperature detected: temperature=' + str(temperature)  + ' turning on AC' )

    toggle_ac()


main()

