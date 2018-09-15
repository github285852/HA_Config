from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity

import voluptuous as vol
import threading
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'zq1112wg'

CONF_GATEWAY_DEV = '/dev/ttyUSB0'
CONF_INTERFACE = 'interface'
DEFAULT_BAUDE = 115200
CONF_TYPE = 'type'
CONF_NAME = 'name'
CONF_DATA = 'data'
CONF_ADDR = 'addr'
CONF_DEVICE = 'device'
CONF_SWITCH = 'switch'
CONF_SENSOR = 'sensor'
CONF_BAUDE = 'baude'
DEFAULT_DATA = '123'
DEFAULT_ADDR = '123'
DEVICE_SCHEMA = vol.Schema([
	vol.Schema({
		vol.Required(CONF_TYPE): cv.string,
		vol.Required(CONF_NAME): cv.string,
		vol.Optional(CONF_DATA,default=DEFAULT_DATA): cv.string,
		vol.Optional(CONF_ADDR,default=DEFAULT_ADDR): cv.string
	})
])

CONFIG_SCHEMA = vol.Schema({
	DOMAIN: vol.Schema({
		vol.Optional(CONF_INTERFACE, default=CONF_GATEWAY_DEV):cv.string,
		vol.Optional(CONF_BAUDE, default=DEFAULT_BAUDE):cv.string,
		vol.Optional(CONF_DEVICE, default=[]):DEVICE_SCHEMA
	})
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
	"""Your controller/hub specific code."""
	_LOGGER.info("setup zq1112wg component")
	from gateway import ZQGateway 	
	zq1112wg = ZQGateway(config.get(DOMAIN,{}).get(CONF_INTERFACE,''),DEFAULT_BAUDE)
	devices = config.get(DOMAIN,{}),get(CONF_DEVICE,[])
	for device in devices:
		type = device.get(CONF_TYPE,'')
		if type == CONF_SWITCH:
			_LOGGER.info("read switch,name:%s,data:%s",device.get(CONF_NAME,''),device.get(CONF_DATA))
		elif type == CONF_SENSOR:
			_LOGGER.info("read sensor,name:%s,addr:%s",device.get(CONF_NAME,''),device.get(CONF_ADDR))
	hass.data[DOMAIN] = zq1112wg  #add key of dict

	def stop(event):
		"""Stop the listener queue and clean up."""
		print('stop zq1112wg event')
		nonlocal zq1112wg
		zq1112wg.ser.close()
		zq1112wg = None
		_LOGGER.info("Waiting for long poll to zq1112wg to time out")

	hass.bus.listen(EVENT_HOMEASSISTANT_STOP,stop)
	return True


