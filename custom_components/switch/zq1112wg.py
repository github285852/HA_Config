from homeassistant.helpers.entity import Entity
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice #switch component the platform name as file
from homeassistant.helpers.entity import ToggleEntity
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging
from homeassistant.const import CONF_NAME
import sys
sys.path.append('/home/pi')
import gateway

from gateway.gateway import ZQGateway
import platform

CONF_DATA = 'data'
CONF_TIMERS = 'timers'
CONF_DEV = 'dev'
CONF_BAUDE = 'baude'

DEFAULT_NAME = 'default_name'
DEFAULT_TIMERS = 4
DEFAULT_DEV = '/dev/ttyUSB0'
DEFAULT_BAUDE = 115200

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Optional(CONF_NAME,default=DEFAULT_NAME): cv.string,
	vol.Required(CONF_DATA):cv.string,
	vol.Optional(CONF_DEV,default=DEFAULT_DEV): cv.string,
	vol.Optional(CONF_BAUDE,default=DEFAULT_BAUDE): cv.string,
	vol.Optional(CONF_TIMERS,default = DEFAULT_TIMERS):
		vol.All(vol.Coerce(int),vol.Range(min=1, max=10)),
})


def setup_platform(hass,config,add_devices,discovery_info=None):
	"""setup the switch platform."""
	Name = config.get(CONF_NAME)
	Data = config.get(CONF_DATA)
	Timers = config.get(CONF_TIMERS)
	Dev = config.get(CONF_DEV)
	Badue = int(config.get(CONF_BAUDE))
	try:
		gateway = ZQGateway(Dev,Badue)
	#	gateway = ZQGateway(CONF_DEV,CONF_BAUDE)
	except:
		 _LOGGER.exception("Unable to open serial port for:" )
	switchs = []
	switchs.append(ZQ1112WGSwitch(gateway,Name,Data,Timers))	
	add_devices(switchs)
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
		self._zq1112wg.write_rf433(self._data,self._timers)
		#self._state = True
		#self.schedule_update_ha_state()

	def turn_off(self):
		self._zq1112wg.write_rf433(self._data,self._timers)
		#self._state = False
		#self.schedule_update_ha_state()





