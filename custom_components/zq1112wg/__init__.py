from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.loader import bind_hass
from homeassistant.const import (
	EVENT_HOMEASSISTANT_STOP, EVENT_HOMEASSISTANT_START,SERVICE_TURN_ON,
	ATTR_ENTITY_ID,SERVICE_TURN_OFF)
import voluptuous as vol
import threading
import logging

import sys
sys.path.append('/home/pi')
import asyncio
from gatewayio.gatewayio import async_ZQGateway

_LOGGER = logging.getLogger(__name__)

DOMAIN = "zq1112wg"
DEV_SERVICE_SCHEMA = vol.Schema({
	vol.Optional(ATTR_ENTITY_ID):cv.entity_ids,
})


CONF_GATEWAY_DEV = '/dev/ttyUSB0'
CONF_INTERFACE = 'interface'
DEFAULT_BAUDE = 115200
CONF_TYPE = 'type'
CONF_NAME = 'name'
CONF_DATA = 'data'
CONF_ADDR = 'addr'
CONF_TIMERS = 'timers'
CONF_DEVICE = 'device'
CONF_SWITCH = 'switch'
CONF_SENSOR = 'sensor'
CONF_BAUDE = 'baude'
DEFAULT_DATA = '123'
DEFAULT_ADDR = '123'
DEFAULT_TIMERS = 4

DEVICE_SCHEMA = vol.Schema([
        vol.Schema({
                vol.Required(CONF_TYPE): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_DATA,default=DEFAULT_DATA): cv.string,
                vol.Optional(CONF_ADDR,default=DEFAULT_ADDR): cv.string,
                vol.Optional(CONF_TIMERS,default = DEFAULT_TIMERS):
                        vol.All(vol.Coerce(int),vol.Range(min=1, max=10)),
        })
])

CONFIG_SCHEMA = vol.Schema({
        DOMAIN: vol.Schema({
                vol.Optional(CONF_INTERFACE, default=CONF_GATEWAY_DEV):cv.string,
                vol.Optional(CONF_BAUDE, default=DEFAULT_BAUDE):cv.string,
                vol.Optional(CONF_DEVICE, default=[]):DEVICE_SCHEMA
        })
}, extra=vol.ALLOW_EXTRA)


@bind_hass
def is_on(hass,entity_id=None):
        """Return if the dev is on on based on the statemachine.
        Async friendly.
        """
        return hass.states.is_state(entity_id,STATE_ON)

@bind_hass
def turn_on(hass,entity_id=None):
        """Turn all or specified dev on."""
        hass.add_job(async_turn_on,hass,entity_id)

@callback
@bind_hass
def async_turn_on(hass,entity_idd=None):
        data = {ATTR_ENTITY_ID:entity_id} if entity_id else None
        hass.async_add_job(hass.services.async_call(DOMAIN,SEVICE_TURN_ON,data))

@bind_hass
def turn_off(hass,entity_id=None):
        """Turn all or specified dev on."""
        hass.add_job(async_turn_off,hass,entity_id)

@callback
@bind_hass
def async_turn_off(hass,entity_idd=None):
        data = {ATTR_ENTITY_ID:entity_id} if entity_id else None
        hass.async_add_job(hass.services.async_call(DOMAIN,SEVICE_TURN_OFF,data))

#asyncio.coroutine
async def async_setup(hass, config):
        """Your controller/hub specific code."""
        component = EntityComponent(_LOGGER, DOMAIN, hass)
        _LOGGER.info("setup zq1112wg component")
        zq1112wg = async_ZQGateway()
        await zq1112wg.init(config.get(DOMAIN,{}).get(CONF_INTERFACE,''),DEFAULT_BAUDE)
        devices = config.get(DOMAIN,{}).get(CONF_DEVICE,[])
        dev = []
        for device in devices:
                type = device.get(CONF_TYPE,'')
                if type == CONF_SWITCH:
                        _LOGGER.warning("read switch,name:%s,data:%s",device.get(CONF_NAME,''),device.get(CONF_DATA))
                   #     hass.states.async_set(DOMAIN+"."+device.get(CONF_NAME,''),"on",attributes = device)
                        Name = device.get(CONF_NAME,'')
                        Data = device.get(CONF_DATA,DEFAULT_DATA)
                        Timers = device.get(CONF_TIMERS,DEFAULT_TIMERS)
                        dev.append(ZQ1112WGSwitch(zq1112wg,Name,Data,Timers))
                elif type == CONF_SENSOR:
                        _LOGGER.warning("read sensor,name:%s,addr:%s",device.get(CONF_NAME,''),device.get(CONF_ADDR))
                        hass.states.async_set(DOMAIN+"."+device.get(CONF_NAME,''),"on",attributes = device)
        #hass.data[DOMAIN] = zq1112wg  #add key of dict
        _LOGGER.info("add_entites start")
        await component.async_add_entities(dev)
        _LOGGER.info("add_entites end")
        @asyncio.coroutine
        def async_handle_service(service):
                target_devices = component.async_extract_from_service(service)
                update_tasks = []
                _LOGGER.info("zq1112wg handle service devices")
                for dev in target_devices:	
                        _LOGGER.info("dev: %s, service is %s",str(dev),str(service.service))
                        if service.service == SERVICE_TURN_ON:
                                _LOGGER.info("do on")
                                yield from dev.async_turn_on()

                        elif service.service == SERVICE_TURN_OFF:
                                _LOGGER.info("do off")
                                yield from dev.async_turn_off()
			
                        if not dev.should_poll:
                                continue
                        update_tasks.append(dev.async_update_ha_state(True))

        hass.services.async_register(DOMAIN,SERVICE_TURN_ON,
		async_handle_service,schema=DEV_SERVICE_SCHEMA)
        hass.services.async_register(DOMAIN,SERVICE_TURN_OFF,
                async_handle_service,schema=DEV_SERVICE_SCHEMA)

        def stop(event):
                """Stop the listener queue and clean up."""
                nonlocal zq1112wg
#                zq1112wg.ser.close()
                zq1112wg = None
                _LOGGER.info("Waiting for long poll to zq1112wg to time out")

        _LOGGER.info("listern start")
        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP,stop)
        _LOGGER.info("listen end")
        return True

class ZQ1112WGSwitch(ToggleEntity):
        """Representation of a switch"""
        def __init__(self,zq1112wg,name,data,timers):
                self._zq1112wg = zq1112wg
                self._name = name
                self._data = data
                self._timers = timers
                self._state = True

        @property
        def should_poll(self):
                return False

        @property
        def unique_id(self):
                return self._name

        @property
        def name(self):
                return self._name

        @property
        def is_on(self):
                return self._state

        def turn_on(self):
#                self._zq1112wg.write_rf433(self._data,self._timers)
                self._state = True
                self.schedule_update_ha_state()

        def turn_off(self):
#                self._zq1112wg.write_rf433(self._data,self._timers)
                self._state = False
                self.schedule_update_ha_state()

        @asyncio.coroutine
        def async_turn_on(self, **kwargs):
                """Turn the device on asynchronously."""
                _LOGGER.debug("Turning on: %s", self._name)
                self._state = True
                yield from self._zq1112wg.async_write_rf433(self._data,self._timers)
                self.async_schedule_update_ha_state()

        @asyncio.coroutine
        def async_turn_off(self, **kwargs):
                """Turn the device off asynchronously."""
                _LOGGER.debug("Turning off: %s", self._name)
                self._state = False
                yield from self._zq1112wg.async_write_rf433(self._data,self._timers)
                self.async_schedule_update_ha_state()

