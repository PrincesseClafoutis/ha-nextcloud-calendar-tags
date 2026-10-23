"""Config flow pour Nextcloud Calendar Tags."""
import voluptuous as vol
import caldav
from homeassistant import config_entries

from .const import DOMAIN

class NextcloudCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer la configuration via l'interface utilisateur."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                client = caldav.DAVClient(
                    url=user_input["url"],
                    username=user_input["username"],
                    password=user_input["password"],
                )
                await self.hass.async_add_executor_job(client.principal)
                
                return self.async_create_entry(title="Nextcloud Calendar", data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("url"): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )