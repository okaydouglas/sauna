# sauna

The overarching controller for the home automation setup.

## Management

The soar client manages a soar server daemon, that in turn runs the lights.

soar --red|green|blue --faint|dim|dark  --start | --restart | --shutdown


## TODO

Implement the following command/sets:

+ Shutdown Computer

+ Shutdown rhasspy/voice-assistant  "Shut yourself down..."

+ Turn music on/off.  [Tell it Play "Song" or "Album" or "Playlist"]

+ Pause music, video, movie, anything in a player really.

+ Scenes {morning, night, sleeping, et al.}

  + "I'm going to bed."   {turn off TV, turn off lights, nighttime ambiance}

  + "Good morning!"  {turn on the lights}

+ "Make a list...", "Add to an existing list..."

+ "Set a timer, remind me in n-minutes, x-days..."

+ change brightness of lights [faint, dim, dark, % or absolute value]

+ create an interruption (plays a tone, and waits for a response)

+ create an optimized light controller with:

  +  presets (--red, --yellow, --faint, --bright, ...)

  + --rgbb (red greeb blue + brightness)

  + candle mode/flicker

## Feature Requests

Create a web page that gives you the option to:

+ Turn the AC on/off
  + :: assign AC boundary low/high
  + :: assign AC temperature during cooling/warming cycle
  + :: assign AC fan speed
  + :: toggle AC light on/off

+ Turn the TV on/off
  + :: assign the TV brightness and picture mode

+ Turn the sauna on/off
  + turn the sauna.lights on/off
  + turn the sauna heaters, 1-3 on/off

+ Turn the lights on/off/color/brightness
  + turn the fan lights on/off/color/brightness
  + turn the ceiling lights on/off/color/brightness

+ Start/Stop Sleep cycle

+ Present:
  + Room Temperature/Humidity
  + Sauna Temperature
  + Outdoor Temperature
  + AC "state"

+ Shutdown soard



## Completed Features

+ [x] TV on/off.

+ [x] Turn lights on/off.

+ [x] Change color of lights [bright-white, cool-white, warm-white, red, green, blue, purple, yellow, black-light]

+ [x] "Find my phone", "Where's the phone?"

+ [x] ctrl-c handler that gracefully shuts down lights and heaters

+ [x] an external command to power off sauna heaters (sauna-off)


## Dependencies

Uses the tenacity and aiohttp packages:

```
$ pip install tenacity
$ pip install aiohttp
```


## Credits

We are using [this link](https://restfulapi.net/http-status-codes/) to document HTTP return codes.