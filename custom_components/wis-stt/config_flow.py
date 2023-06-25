import homeassistant.helpers.config_validation as cv
import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None, errors=None):
        if user_input is not None:
            try:
                return self.async_create_entry(title=f"WIS STT ({user_input['url']})", data=user_input)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required("url", default="https://localhost:19000/api/willow"): cv.string,
                    vol.Required("cert_validation", default=True): cv.boolean,
                    vol.Optional("model", default="medium"): cv.string,
                    vol.Optional("detect_language", default=False): cv.boolean,
                    vol.Optional("language", default="en"): cv.string,
                    vol.Optional("beam_size", default=1): cv.port,
                    vol.Optional("speaker", default="CLB"): cv.string,
                    vol.Optional("save_audio", default=False): cv.boolean
                }
            ), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None, errors=None):
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required("url", default=self.config_entry.data["url"]): cv.string,
                    vol.Required("cert_validation", default=self.config_entry.data["cert_validation"]): cv.boolean,
                    vol.Optional("model", default=self.config_entry.data["model"]): cv.string,
                    vol.Optional("detect_language", default=self.config_entry.data["detect_language"]): cv.boolean,
                    vol.Optional("language", default=self.config_entry.data["language"]): cv.string,
                    vol.Optional("beam_size", default=self.config_entry.data["beam_size"]): cv.port,
                    vol.Optional("speaker", default=self.config_entry.data["speaker"]): cv.string,
                    vol.Optional("save_audio", default=self.config_entry.data["save_audio"]): cv.boolean
                }
            ), errors=errors
        )

    async def async_step_user(self, user_input: None, errors=None):
        try:
            self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
            return self.async_create_entry(title=None, data=None)
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"