from core.rules import rule
from core.triggers import when
from core.utils import sendCommand, postUpdate
from core.date import seconds_between
from core.actions import ScriptExecution
createTimer = ScriptExecution.createTimer
from org.joda.time import DateTime

pit_relays = [
    "pool_pit_relay_up",
    "pool_pit_relay_down",
    "pool_pit_relay_in",
    "pool_pit_relay_out"
]

float_delay = 10 # seconds
float_last_change = {
    "fill_lower": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
    "fill_upper": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
    "overfill_lower": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
    "overfill_upper": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
}
float_timer = {
    "fill": None,
    "overfill": None
}

timer_acid = None

timer_umbrella = None


@rule("Pool Pit Cover Control")
@when("Item pool_pit_state received command")
@when("Item pool_pit_switch_up received update")
@when("Item pool_pit_switch_down received update")
@when("Item pool_pit_switch_in received update")
@when("Item pool_pit_switch_out received update")
def rule_pool_pit_control(event):
    def relays_off(skip=None):
        for name in pit_relays:
            if name != skip:
                sendCommand(name, OFF)

    log = rule_pool_pit_control.log # simplify log access
    state = str(items["pool_pit_state"]) # get currect state
    switch = { # get switch states
        "up": True if items["pool_pit_switch_up"] == ON else False,
        "down": True if items["pool_pit_switch_down"] == ON else False,
        "in": True if items["pool_pit_switch_in"] == ON else False,
        "out": True if items["pool_pit_switch_out"] == ON else False,
    }

    # a command was sent
    if event.itemName == "pool_pit_state":
        # already in the state requested
        if event.itemCommand == state:
            log.debug("Pool Pit is already {}".format(event.itemCommand))
            return
        # new command
        state = event.itemCommand[:4] + "ing"

    # a switch changed
    else:
        switch[event.itemName.split("_")[-1]] = True if event.itemState == ON else False

    # pit is opening
    if state == "opening":
        # pit has finished opening
        if switch["up"] and switch["out"]:
            relays_off()
            postUpdate("pool_pit_state", "open")
            #log.info("Pool Pit is now open")
        # pit has finished moving up
        elif switch["up"]:
            relays_off("pool_pit_relay_out")
            sendCommand("pool_pit_relay_out", ON)
            postUpdate("pool_pit_state", "opening")
            log.debug("Pool Pit is moving out")
        # pit needs to move up
        else:
            relays_off("pool_pit_relay_up")
            sendCommand("pool_pit_relay_up", ON)
            postUpdate("pool_pit_state", "opening")
            log.debug("Pool Pit is moving up")

    # pit is closing
    elif state == "closing":
        # pit has finished closing
        if switch["down"] and switch["in"]:
            relays_off()
            postUpdate("pool_pit_state", "close")
            #log.info("Pool Pit is now closed")
        # pit has finished moving in
        elif switch["in"]:
            relays_off("pool_pit_relay_down")
            sendCommand("pool_pit_relay_down", ON)
            postUpdate("pool_pit_state", "closing")
            log.debug("Pool Pit is moving down")
        # pit needs to move in
        else:
            relays_off("pool_pit_relay_in")
            sendCommand("pool_pit_relay_in", ON)
            postUpdate("pool_pit_state", "closing")
            log.debug("Pool Pit is moving in")

    # stop requested
    elif state == "stoping":
        relays_off()
        postUpdate("pool_pit_state", "stop")
        log.info("Pool Pit is now stopped")




def timer_umbrella_up(log):
    log.info("The Umbrella is now Opening")
    sendCommand("pool_umbrelladown", OFF)
    log.info("Oening the Umbrella")
    sendCommand("pool_umbrellaup", ON)
    global timer_umbrella
    timer_umbrella = createTimer(DateTime.now().plusSeconds(45), lambda: timer_umbrella_up(log))

def timer_umbrlla_down(log):
    log.info("The umbrella is now Closing")
    sendCommand("pool_umbrellaup", OFF)
    log.info("Closeing the Umbrella")
    sendCommand("pool_umbrelladown", ON)
    global timer_umbrella
    timer_umbrella = createTimer(DateTime.now().plusSeconds(45), lambda: timer_umbrlla_down(log))

@rule("Pool Umbrella", description="Sends commands to the umbrella actuator")
@when("Item pool_umbrellaup received command")
@when("Item pool_umbrelladown received command")
@when("Item pool_umbrella received command")
def umbrella_command(event):
    log = umbrella_command.log

    if str(event.itemCommand) == "open":
        if items["pool_umbrellaup"] == OFF:
            log.info("Opening Pool Umbrella")
            sendCommand("pool_umbrelladown", "OFF")
            sendCommand("pool_umbrellaup", "ON")
            #sendCommand("POOLCONTROL/umbrella/relay/down/set", "OFF")
            #sendCommand("POOLCONTROL/umbrella/relay/up/pulse", "120000, ON")

    elif str(event.itemCommand) == "close":
        if items["pool_umbrelladown"] == OFF:
            log.info("Closing Pool Umbrella")
            sendCommand("pool_umbrellaup", "OFF")
            sendCommand("pool_umbrelladown", "ON")
            #sendCommand("POOLCONTROL/umbrella/relay/down/pulse", "120000, ON")
              #sendCommand("POOLCONTROL/umbrella/relay/up/set", "OFF")

    elif str(event.itemCommand) == "stop":
        if items["pool_umbrelladown"] == ON:
            log.info("Stopping Pool Umbrella")
            sendCommand("pool_umbrellaup", "OFF")
            sendCommand("pool_umbrelladown", "OFF")

    elif str(event.itemCommand) == "stop":
        if items["pool_umbrelladoup"] == ON:
            log.info("Stopping Pool Umbrella")
            sendCommand("pool_umbrellaup", "OFF")
            sendCommand("pool_umbrelladown", "OFF")

"""
    elif str(event.itemCommand) == "stop":
        if  items["pool_umbrellaup"] == ON:
            log.info("Stopping Pool Umbrella")
            sendCommand("pool_umbrellaup", "OFF")
            sendCommand("pool_umbrelladown", "OFF")


    else: 
            str (event.itemCommand) == "stop"
            log.info("Stopping Pool Umbrella")
            sendCommand("pool_umbrelladown", "OFF")
            sendCommand("pool_umbrellaup", "OFF")
       

        #sendCommand("POOLCONTROL/umbrella/relay/up/set", "OFF")
        #sendCommand("POOLCONTROL/umbrella/relay/down/set", "OFF")
 # mqtt = actions.get("mqtt", "mqtt:broker:home")

"""

@rule("Rule Low Water Warning", description="Warning light and notification when low water is detected")
@when("Item pool_floatSW_low_water changed")
def low_water_level(event):
    if items["pool_floatSW_low_water"] == OFF:
        sendCommand("pool_low_water", ON)
        low_water_level.log.warn("Send Help, Low Water Level!")
    else:
        sendCommand("pool_low_water", OFF)

@rule("Rule Low Acid Level Warning", description="Warning light and notification when low acid level is detected")
@when("Item pool_floatSW_acid_levellow changed")
def low_acid__level(event):
    if items["pool_floatSW_acid_lwvellow"] == OFF:
        sendCommand("pool_acid_levellow", ON)
        low_water_level.log.warn("Send Help, Low Acid Level!")
    else:
        sendCommand("pool_acid_levellow", OFF)


@rule("Pool Water Level Low", description="This turns on the filling relay if the water level is low")
@when("Item pool_floatSW_fill_lower received update")
@when("Item pool_floatSW_fill_upper received update")
def rule_water_low(event):
    log = rule_water_low.log
    fill_lower = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_fill_lower" else items["pool_floatSW_fill_lower"]) == ON else False
    fill_upper = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_fill_upper" else items["pool_floatSW_fill_upper"]) == ON else False
    now = DateTime.now()

    # check if switch changed and update it's last changed time if it did
    if fill_lower != float_last_change["fill_lower"]["state"]:
        float_last_change["fill_lower"]["time"] = now
        float_last_change["fill_lower"]["state"] = fill_lower
    if fill_upper != float_last_change["fill_upper"]["state"]:
        float_last_change["fill_upper"]["time"] = now
        float_last_change["fill_upper"]["state"] = fill_upper

    # check if lower switch has changed within the delay period
    if now.isBefore(float_last_change["fill_lower"]["time"].plusSeconds(float_delay)):
        if float_timer["fill"] and not float_timer["fill"].hasTerminated():
            float_timer["fill"].cancel()

    # check if upper switch has changed within the delay period
    elif now.isBefore(float_last_change["fill_upper"]["time"].plusSeconds(float_delay)):
        if float_timer["fill"] and not float_timer["fill"].hasTerminated():
            float_timer["fill"].cancel()
        float_timer["fill"] = createTimer(
            now.plusSeconds(seconds_between(now, float_last_change["fill_upper"]["time"].plusSeconds(float_delay + 1))),
            lambda: rule_water_low(None)
        )

    # neither switch changed recently, lets take action
    else:
        # lower and upper switches are on
        if fill_lower and fill_upper:
            # pump is on
            if items["pool_waterfill"] == ON:
                log.info("Turning OFF pool filling relay")
                sendCommand("pool_waterfill", OFF)

        # lower and upper switches are off
        elif not fill_lower and not fill_upper:
            # pump is off
            if items["pool_waterfill"] == OFF:
                log.warn("Pool water level is low!")
                log.info("Turning ON pool filling relay")
                sendCommand("pool_waterfill", ON)

        # incorrect state, warn and turn off pump
        if not fill_lower and fill_upper:
            log.error("Pool low level switches in an impossible state!")
            log.error("Upper low level float switch is ON but lower float switch is OFF")
            sendCommand("pool_waterfill", OFF)
            sendCommand("pool_fill_error", ON)
        else:
            sendCommand("pool_fill_error", OFF)


@rule("Pool Water Level High", description="This turns on the emptying relay if the water level is high")
@when("Item pool_floatSW_overfill_lower received update")
@when("Item pool_floatSW_overfill_upper received update")
def rule_water_high(event):
    log = rule_water_high.log
    overfill_lower = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_overfill_lower" else items["pool_floatSW_overfill_lower"]) == ON else False
    overfill_upper = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_overfill_upper" else items["pool_floatSW_overfill_upper"]) == ON else False
    now = DateTime.now()

    # check if switch changed and update it's last changed time if it did
    if overfill_lower != float_last_change["overfill_lower"]["state"]:
        float_last_change["overfill_lower"]["time"] = now
        float_last_change["overfill_lower"]["state"] = overfill_lower
    if overfill_upper != float_last_change["overfill_upper"]["state"]:
        float_last_change["overfill_upper"]["time"] = now
        float_last_change["overfill_upper"]["state"] = overfill_upper

    # check if lower switch has changed within the delay period
    if now.isBefore(float_last_change["overfill_lower"]["time"].plusSeconds(float_delay)):
        if float_timer["overfill"] and not float_timer["overfill"].hasTerminated():
            float_timer["overfill"].cancel()
        float_timer["overfill"] = createTimer(
            now.plusSeconds(seconds_between(now, float_last_change["overfill_lower"]["time"].plusSeconds(float_delay + 1))),
            lambda: rule_water_high(None)
        )

    # check if upper switch has changed within the delay period
    elif now.isBefore(float_last_change["overfill_upper"]["time"].plusSeconds(float_delay)):
        if float_timer["overfill"] and not float_timer["overfill"].hasTerminated():
            float_timer["overfill"].cancel()
        float_timer["overfill"] = createTimer(
            now.plusSeconds(seconds_between(now, float_last_change["overfill_upper"]["time"].plusSeconds(float_delay + 1))),
            lambda: rule_water_high(None)
        )

    # neither switch changed recently, lets take action
    else:
        # lower and upper switches are on
        if overfill_lower and overfill_upper:
            # pump is off
            if items["pool_wateroverfill"] == OFF:
                log.warn("Pool water level is high!")
                log.info("Turning ON pool emptying relay")
                sendCommand("pool_wateroverfill", ON)

        # lower and upper switches are off
        elif not overfill_lower and not overfill_upper:
            # pump is on
            if items["pool_wateroverfill"] == ON:
                log.info("Turning OFF pool emptying relay")
                sendCommand("pool_wateroverfill", OFF)

        # incorrect state, warn and turn off pump
        if not overfill_lower and overfill_upper:
            log.error("Pool high level switches in an impossible state!")
            log.error("Upper high level float switch is ON but lower float switch is OFF")
            sendCommand("pool_wateroverfill", OFF)
            sendCommand("pool_overfill_error", ON)
        else:
            sendCommand("pool_overfill_error", OFF)
"""
@rule("Rule Acid Pump Flush", description="When the waterfill relay has turned off, it runs the Acid pump in reverse to flush with clean water")
@when("Item pool_waterfill changed")
def Acid_pump_flush(event):
    Acid_pump_flush.log.info("Acid pump state: {}".format(items["pool_acidpump"]))
    Acid_pump_flush.log.info("Flushing the Acid Pump")
    if items["pool_waterfill"] == OFF:
        sendCommand("pool_acidpumpflush", ON)
    else:
        sendCommand("pool_acidpumpflush", (OFF))
"""


def timer_flushdone(log):
    log.info("Done acid pump backflush")
    sendCommand("pool_acidpumpflush", OFF)
    log.info("Acid injection secquence completed")
    sendCommand("pool_acidinject", OFF)
    global timer_acid
    timer_acid = None

def timer_acidflush(log):
    log.info("Done flushing water line")
    sendCommand("pool_waterfill", OFF)
    log.info("Backflushing acid pump")
    sendCommand("pool_acidpumpflush", ON)
    global timer_acid
    timer_acid = createTimer(DateTime.now().plusSeconds(10), lambda: timer_flushdone(log))

def timer_fillflush(log):
    log.info("Acid injection done")
    sendCommand("pool_acidpump", OFF)
    log.info("Flushing water line")
    sendCommand("pool_waterfill", ON)
    global timer_acid
    timer_acid = createTimer(DateTime.now().plusSeconds(10), lambda: timer_acidflush(log))

@rule("Rule Acid Injection", description="")
@when("Item pool_acidinject received command ON")
def rule_acidinject(event):
    global timer_acid
    if timer_acid is None:
        rule_acidinject.log.info("Injecting 250ml of acid")
        sendCommand("pool_acidpump", ON)
        timer_acid = createTimer(DateTime.now().plusSeconds(45), lambda: timer_fillflush(rule_acidinject.log))
    else:
        rule_acidinject.log.warn("Failed to start acid flush, an acid flush sequence is already running")

def scriptUnloaded():
    if timer_acid is not None and not timer_acid.hasTerminated():
        timer_acid.cancel()
"""

from core.rules import rule
from core.triggers import when
from core.utils import sendCommand, postUpdate
from core.date import seconds_between
from core.actions import ScriptExecution
createTimer = ScriptExecution.createTimer
from org.joda.time import DateTime

timer_acid = None

pit_relays = [
    "pool_pit_relay_up",
    "pool_pit_relay_down",
    "pool_pit_relay_in",
    "pool_pit_relay_out"
]

float_delay = 10 # seconds
float_last_change = {
    "fill_lower": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
    "fill_upper": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
    "overfill_lower": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
    "overfill_upper": {"time": DateTime.now().withTimeAtStartOfDay(), "state": None},
}
float_timer = {
    "fill": None,
    "overfill": None
}



@rule("Pool Pit Cover Control")
@when("Item pool_pit_state received command")
@when("Item pool_pit_switch_up received update")
@when("Item pool_pit_switch_down received update")
@when("Item pool_pit_switch_in received update")
@when("Item pool_pit_switch_out received update")
def rule_pool_pit_control(event):
    def relays_off(skip=None):
        for name in pit_relays:
            if name != skip:
                sendCommand(name, OFF)

    log = rule_pool_pit_control.log # simplify log access
    state = str(items["pool_pit_state"]) # get currect state
    switch = { # get switch states
        "up": True if items["pool_pit_switch_up"] == ON else False,
        "down": True if items["pool_pit_switch_down"] == ON else False,
        "in": True if items["pool_pit_switch_in"] == ON else False,
        "out": True if items["pool_pit_switch_out"] == ON else False,
    }

    # a command was sent
    if event.itemName == "pool_pit_state":
        # already in the state requested
        if event.itemCommand == state:
            log.debug("Pool Pit is already {}".format(event.itemCommand))
            return
        # new command
        state = event.itemCommand[:4] + "ing"

    # a switch changed
    else:
        switch[event.itemName.split("_")[-1]] = True if event.itemState == ON else False

    # pit is opening
    if state == "opening":
        # pit has finished opening
        if switch["up"] and switch["out"]:
            relays_off()
            postUpdate("pool_pit_state", "open")
            #log.info("Pool Pit is now open")
        # pit has finished moving up
        elif switch["up"]:
            relays_off("pool_pit_relay_out")
            sendCommand("pool_pit_relay_out", ON)
            postUpdate("pool_pit_state", "opening")
            log.debug("Pool Pit is moving out")
        # pit needs to move up
        else:
            relays_off("pool_pit_relay_up")
            sendCommand("pool_pit_relay_up", ON)
            postUpdate("pool_pit_state", "opening")
            log.debug("Pool Pit is moving up")

    # pit is closing
    elif state == "closing":
        # pit has finished closing
        if switch["down"] and switch["in"]:
            relays_off()
            postUpdate("pool_pit_state", "close")
            #log.info("Pool Pit is now closed")
        # pit has finished moving in
        elif switch["in"]:
            relays_off("pool_pit_relay_down")
            sendCommand("pool_pit_relay_down", ON)
            postUpdate("pool_pit_state", "closing")
            log.debug("Pool Pit is moving down")
        # pit needs to move in
        else:
            relays_off("pool_pit_relay_in")
            sendCommand("pool_pit_relay_in", ON)
            postUpdate("pool_pit_state", "closing")
            log.debug("Pool Pit is moving in")

    # stop requested
    elif state == "stoping":
        relays_off()
        postUpdate("pool_pit_state", "stop")
        log.info("Pool Pit is now stopped")


@rule("Pool Umbrella", description="Sends commands to the umbrella actuator")
@when("Item pool_umbrella received command")
def umbrella_command(event):
    log = umbrella_command.log
    mqtt = actions.get("mqtt", "mqtt:broker:home")

    if str(event.itemCommand) == "open":
        if items["pool_umbrella_relay_up"] == OFF:
            log.info("Opening Pool Umbrella")
            #sendCommand("pool_umbrella_down", OFF)
            mqtt.publishMQTT("POOLCONTROL/umbrella/relay/down/set", "OFF")
            #sendCommand("pool_umbrella_up", ON)
            mqtt.publishMQTT("POOLCONTROL/umbrella/relay/up/pulse", "120000, ON")
    elif str(event.itemCommand) == "close":
        if items["pool_umbrella_relay_down"] == OFF:
            log.info("Closing Pool Umbrella")
            #sendCommand("pool_umbrella_up", OFF)
            mqtt.publishMQTT("POOLCONTROL/umbrella/relay/up/set", "OFF")
            #sendCommand("pool_umbrella_down", ON)
            mqtt.publishMQTT("POOLCONTROL/umbrella/relay/down/pulse", "120000, ON")
    else:
        log.warn("Stopping Pool Umbrella")
        #sendCommand("pool_umbrella_up", OFF)
        mqtt.publishMQTT("POOLCONTROL/umbrella/relay/up/set", "OFF")
        #sendCommand("pool_umbrella_down", OFF)
        mqtt.publishMQTT("POOLCONTROL/umbrella/relay/down/set", "OFF")


@rule("Rule Low Water Warning", description="Warning light and notification when low water is detected")
@when("Item pool_floatSW_low_water changed")
def low_water_level(event):
    if items["pool_floatSW_low_water"] == OFF:
        sendCommand("pool_low_water", ON)
        low_water_level.log.warn("Send Help, Low Water Level!")
    else:
        sendCommand("pool_low_water", OFF)

@rule("Rule Low Acid Level Warning", description="Warning light and notification when low acid level is detected")
@when("Item pool_floatSW_acid_level_low changed")
def low_acid__level(event):
    if items["pool_floatSW_acid_lwvel_low"] == OFF:
        sendCommand("pool_acid_level_low", ON)
        low_water_level.log.warn("Send Help, Low Acid Level!")
    else:
        sendCommand("pool_acid_level_low", OFF)


@rule("Pool Water Level Low", description="This turns on the filling relay if the water level is low")
@when("Item pool_floatSW_fill_lower received update")
@when("Item pool_floatSW_fill_upper received update")
def rule_water_low(event):
    log = rule_water_low.log
    fill_lower = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_fill_lower" else items["pool_floatSW_fill_lower"]) == ON else False
    fill_upper = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_fill_upper" else items["pool_floatSW_fill_upper"]) == ON else False
    now = DateTime.now()

    # check if switch changed and update it's last changed time if it did
    if fill_lower != float_last_change["fill_lower"]["state"]:
        float_last_change["fill_lower"]["time"] = now
        float_last_change["fill_lower"]["state"] = fill_lower
    if fill_upper != float_last_change["fill_upper"]["state"]:
        float_last_change["fill_upper"]["time"] = now
        float_last_change["fill_upper"]["state"] = fill_upper

    # check if lower switch has changed within the delay period
    if now.isBefore(float_last_change["fill_lower"]["time"].plusSeconds(float_delay)):
        if float_timer["fill"] and not float_timer["fill"].hasTerminated():
            float_timer["fill"].cancel()

    # check if upper switch has changed within the delay period
    elif now.isBefore(float_last_change["fill_upper"]["time"].plusSeconds(float_delay)):
        if float_timer["fill"] and not float_timer["fill"].hasTerminated():
            float_timer["fill"].cancel()
        float_timer["fill"] = createTimer(
            now.plusSeconds(seconds_between(now, float_last_change["fill_upper"]["time"].plusSeconds(float_delay + 1))),
            lambda: rule_water_low(None)
        )

    # neither switch changed recently, lets take action
    else:
        # lower and upper switches are on
        if fill_lower and fill_upper:
            # pump is on
            if items["pool_waterfill"] == ON:
                log.info("Turning OFF pool filling relay")
                sendCommand("pool_waterfill", OFF)

        # lower and upper switches are off
        elif not fill_lower and not fill_upper:
            # pump is off
            if items["pool_waterfill"] == OFF:
                log.warn("Pool water level is low!")
                log.info("Turning ON pool filling relay")
                sendCommand("pool_waterfill", ON)

        # incorrect state, warn and turn off pump
        if not fill_lower and fill_upper:
            log.error("Pool low level switches in an impossible state!")
            log.error("Upper low level float switch is ON but lower float switch is OFF")
            sendCommand("pool_waterfill", OFF)
            sendCommand("pool_fill_error", ON)
        else:
            sendCommand("pool_fill_error", OFF)


@rule("Pool Water Level High", description="This turns on the emptying relay if the water level is high")
@when("Item pool_floatSW_overfill_lower received update")
@when("Item pool_floatSW_overfill_upper received update")
def rule_water_high(event):
    log = rule_water_high.log
    overfill_lower = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_overfill_lower" else items["pool_floatSW_overfill_lower"]) == ON else False
    overfill_upper = True if (event.itemState if getattr(event, "itemName", None) == "pool_floatSW_overfill_upper" else items["pool_floatSW_overfill_upper"]) == ON else False
    now = DateTime.now()

    # check if switch changed and update it's last changed time if it did
    if overfill_lower != float_last_change["overfill_lower"]["state"]:
        float_last_change["overfill_lower"]["time"] = now
        float_last_change["overfill_lower"]["state"] = overfill_lower
    if overfill_upper != float_last_change["overfill_upper"]["state"]:
        float_last_change["overfill_upper"]["time"] = now
        float_last_change["overfill_upper"]["state"] = overfill_upper

    # check if lower switch has changed within the delay period
    if now.isBefore(float_last_change["overfill_lower"]["time"].plusSeconds(float_delay)):
        if float_timer["overfill"] and not float_timer["overfill"].hasTerminated():
            float_timer["overfill"].cancel()
        float_timer["overfill"] = createTimer(
            now.plusSeconds(seconds_between(now, float_last_change["overfill_lower"]["time"].plusSeconds(float_delay + 1))),
            lambda: rule_water_high(None)
        )

    # check if upper switch has changed within the delay period
    elif now.isBefore(float_last_change["overfill_upper"]["time"].plusSeconds(float_delay)):
        if float_timer["overfill"] and not float_timer["overfill"].hasTerminated():
            float_timer["overfill"].cancel()
        float_timer["overfill"] = createTimer(
            now.plusSeconds(seconds_between(now, float_last_change["overfill_upper"]["time"].plusSeconds(float_delay + 1))),
            lambda: rule_water_high(None)
        )

    # neither switch changed recently, lets take action
    else:
        # lower and upper switches are on
        if overfill_lower and overfill_upper:
            # pump is off
            if items["pool_wateroverfill"] == OFF:
                log.warn("Pool water level is high!")
                log.info("Turning ON pool emptying relay")
                sendCommand("pool_wateroverfill", ON)

        # lower and upper switches are off
        elif not overfill_lower and not overfill_upper:
            # pump is on
            if items["pool_wateroverfill"] == ON:
                log.info("Turning OFF pool emptying relay")
                sendCommand("pool_wateroverfill", OFF)

        # incorrect state, warn and turn off pump
        if not overfill_lower and overfill_upper:
            log.error("Pool high level switches in an impossible state!")
            log.error("Upper high level float switch is ON but lower float switch is OFF")
            sendCommand("pool_wateroverfill", OFF)
            sendCommand("pool_overfill_error", ON)
        else:
            sendCommand("pool_overfill_error", OFF)

@rule("Rule Acid Pump Flush", description="When the waterfill relay has turned off, it runs the Acid pump in reverse to flush with clean water")
@when("Item pool_waterfill changed")
def Acid_pump_flush(event):
    Acid_pump_flush.log.info("Acid pump state: {}".format(items["pool_acidpump"]))
    Acid_pump_flush.log.info("Flushing the Acid Pump")
    if items["pool_waterfill"] == OFF:
        sendCommand("pool_acidpumpflush", ON)
    else:
        sendCommand("pool_acidpumpflush", (OFF))



def timer_flushdone(log):
    log.info("Done acid pump backflush")
    sendCommand("pool_acidpumpflush", OFF)
    log.info("Acid injection secquence completed")
    sendCommand("pool_acidinject", OFF)
    global timer_acid
timer_acid = None

def timer_acidflush(log):
    log.info("Done flushing water line")
    sendCommand("pool_waterfill", OFF)
    log.info("Backflushing acid pump")
    sendCommand("pool_acidpumpflush", ON)
    global timer_acid
timer_acid = createTimer(DateTime.now().plusSeconds(10), lambda: timer_flushdone(log))

def timer_fillflush(log):
    log.info("Acid injection done")
    sendCommand("pool_acidpump", OFF)
    log.info("Flushing water line")
    sendCommand("pool_waterfill", ON)
    global timer_acid
timer_acid = createTimer(DateTime.now().plusSeconds(10), lambda: timer_acidflush(log))

@rule("Rule Acid Injection", description="")
@when("Item pool_acidinject received command ON")
def rule_acidinject(event):
    global timer_acid
if timer_acid is None:
    rule_acidinject.log.info("Injecting 250ml of acid")
    sendCommand("pool_acidpump", ON)
    timer_acid = createTimer(DateTime.now().plusSeconds(45), lambda: timer_fillflush(rule_acidinject.log))
else:
    rule_acidinject.log.warn("Failed to start acid flush, an acid flush sequence is already running")

def scriptUnloaded():
    if timer_acid is not None and not timer_acid.hasTerminated():
        timer_acid.cancel()


@rule("Rule Acid Pump line Flush", description="When the Acid pump relay turns off, the waterfill relay turs on for 10 seconds to flush the line with clean water")
@when("Item pool_acidpump changed")
def Flush_water_line(event):
    Flush_water_line.log.info("Acid pump state: {}".format(items["pool_acidpump"]))
    Flush_water_line.log.info("Flushing the Acid from the ffed lines")
    if items["pool_acidpump"] == OFF:
        sendCommand("pool_waterfill", ON)
        createTimer(DateTime.now().plusSeconds(10), lambda: sendCommand("pool_waterfill", OFF))
    else:
        sendCommand("pool_acidpump", (OFF))

@rule("Rule Acid Pump Run Time", description="When the Acid pump turn on, this is the timer so it runs for 45 seconds putting 250ml of acid into the pool water")
@when("Item pool_acidpump changed")
def Acid_pump_timer(event):
    Acid_pump_timer.log.info("Acid pump state: {}".format(items["pool_acidpump"]))
    Acid_pump_timer.log.info("Running timer for the acid pump")
    if  items["pool_acidpump"] == (ON):
        createTimer(DateTime.now().plusSeconds(45), lambda: sendCommand("pool_acidpump", OFF))
    else:
        sendCommand("pool_acidpump", (OFF))


@rule("pit up stop", description="This rule stops the timer when the pit reaches maximum height")
@when('item pitSWup recieved command ON')
def pit_up_stop(event)
      sendCommand("pool_pit_up"), (OFF))
      stopTimer

@rule ("Pool Cover OUT", description="Second motion pushing the pool cover forward from underneath the PIT cover")
@when ("item pitSWup state=(ON)")
@when ("pool_pit_up recieved command (OFF)")
def  pit_out(event): sendcomand ('pool_pitout ,(ON), ('createTimer (now.plusSeconds(45))) :sendcommand ('pool_pitout (OFF))')
@when   ('item pitSWout recieved comand (ON)')
def pit_out_stop(event) ('stopTimer')

@rule ("Pool Cover In", description="This is the motion that returns the pool cover back undernieth the pit cover")
@when ("item pitSWup stat=(ON)")
@when ("pool_pit_down recieved command (ON)")
def  pit_in(event): sendcomand ('pool_pitin ,(ON), ('createTimer (now.plusSeconds(45))) :sendcommand ('pool_pitin (OFF))')
@when   ('item pitSWin recieved comand (ON)')
def pit_out_stop(event) ('stopTimer')

@rule ("Pit Cover Down", description="This is the motion that returns the pool pit cover back into its cavity")
@when   ('item pitSWin state (ON)')
@when ("pool_pit_in reicieved command (OFF)")
def  pit_in(event): sendcomand ('pool_pitdown ,(ON), ('createTimer (now.plusSeconds(45))) :sendcommand ('pool_pitdown (OFF))')
@when   ('item pitSWdown recieved comand (ON)')
def pit_out_stop(event) ('stopTimer')





/*
rule "relay out"
when
      Item pool_pit_open receivedcommand "OFF"
      pitswitch recievedcomand "ON"
then
        Item pool_pit_out  sendcommand "ON"
        Create Timer(now.plusSeconds(10)) sendcommand(pool_pit_out ,OFF)
        pitswitchout recievedcomand "on", Stop Timer
end


@rule("Rule Acid Pump line Flush", description="When the Acid pump relay turns off, the waterfill relay turs on for 10 seconds to flush the line with clean water")
@when("Item pool_acidpump changed")
def Flush_water_line(event):
    Flush_water_line.log.info("Acid pump state: {}".format(items["pool_acidpump"]))
    Flush_water_line.log.info("Flushing the Acid from the ffed lines")
    if items["pool_acidpump"] == OFF:
        sendCommand("pool_waterfill", ON)
        createTimer(DateTime.now().plusSeconds(10), lambda: sendCommand("pool_waterfill", OFF))
    else:
        sendCommand("pool_acidpump", (OFF))

@rule("Rule Acid Pump Run Time", description="When the Acid pump turn on, this is the timer so it runs for 45 seconds putting 250ml of acid into the pool water")
@when("Item pool_acidpump changed")
def Acid_pump_timer(event):
    Acid_pump_timer.log.info("Acid pump state: {}".format(items["pool_acidpump"]))
    Acid_pump_timer.log.info("Running timer for the acid pump")
    if  items["pool_acidpump"] == (ON):
        createTimer(DateTime.now().plusSeconds(45), lambda: sendCommand("pool_acidpump", OFF))
    else:
        sendCommand("pool_acidpump", (OFF))


@rule("pit up stop", description="This rule stops the timer when the pit reaches maximum height")
@when('item pitSWup recieved command ON')
def pit_up_stop(event)
      sendCommand("pool_pit_up"), (OFF))
      stopTimer

@rule ("Pool Cover OUT", description="Second motion pushing the pool cover forward from underneath the PIT cover")
@when ("item pitSWup state=(ON)")
@when ("pool_pit_up recieved command (OFF)")
def  pit_out(event): sendcomand ('pool_pitout ,(ON), ('createTimer (now.plusSeconds(45))) :sendcommand ('pool_pitout (OFF))')
@when   ('item pitSWout recieved comand (ON)')
def pit_out_stop(event) ('stopTimer')

@rule ("Pool Cover In", description="This is the motion that returns the pool cover back undernieth the pit cover")
@when ("item pitSWup stat=(ON)")
@when ("pool_pit_down recieved command (ON)")
def  pit_in(event): sendcomand ('pool_pitin ,(ON), ('createTimer (now.plusSeconds(45))) :sendcommand ('pool_pitin (OFF))')
@when   ('item pitSWin recieved comand (ON)')
def pit_out_stop(event) ('stopTimer')

@rule ("Pit Cover Down", description="This is the motion that returns the pool pit cover back into its cavity")
@when   ('item pitSWin state (ON)')
@when ("pool_pit_in reicieved command (OFF)")
def  pit_in(event): sendcomand ('pool_pitdown ,(ON), ('createTimer (now.plusSeconds(45))) :sendcommand ('pool_pitdown (OFF))')
@when   ('item pitSWdown recieved comand (ON)')
def pit_out_stop(event) ('stopTimer')
"""



"""
/*
rule "relay out"
when
      Item pool_pit_open receivedcommand "OFF"
      pitswitch recievedcomand "ON"
then
        Item pool_pit_out  sendcommand "ON"
        Create Timer(now.plusSeconds(10)) sendcommand(pool_pit_out ,OFF)
        pitswitchout recievedcomand "on", Stop Timer
end
"""
