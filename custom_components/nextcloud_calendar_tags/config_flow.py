"""Config flow pour Nextcloud Calendar Tags."""
import voluptuous as vol
import caldav
from homeassistant import config_entries
from .const import DOMAIN

def _test_connection_and_get_calendars(url, username, password):
    """Teste la connexion et renvoie la liste des noms de calendriers."""
    client = caldav.DAVClient(
        url=url, username=username, password=password, ssl_verify_cert=False
    ) # type: ignore
    principal = client.principal()
    calendars = principal.calendars()
    return [cal.name for cal in calendars]

class NextcloudCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer la configuration via l'interface utilisateur."""

    VERSION = 1

    def __init__(self):
        """Initialiser le flux."""
        self._url = None
        self._username = None
        self._password = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                # On récupère les calendriers dans l'executor
                calendar_names = await self.hass.async_add_executor_job(
                    _test_connection_and_get_calendars,
                    user_input["url"],
                    user_input["username"],
                    user_input["password"],
                )
                if not calendar_names:
                    errors["base"] = "no_calendars_found"
                else:
                    # On stocke les infos et on passe à l'étape 2
                    self._url = user_input["url"]
                    self._username = user_input["username"]
                    self._password = user_input["password"]
                    return await self.async_step_select_calendar()
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
            ), # type: ignore
            errors=errors,
        )

    async def async_step_select_calendar(self, user_input=None):
        """Deuxième étape : choisir le calendrier."""
        if user_input is not None:
            # On fusionne les infos et on crée l'entrée
            data = {
                "url": self._url,
                "username": self._username,
                "password": self._password,
                "calendar_name": user_input["calendar_name"],
            }
            return self.async_create_entry(title=f"Nextcloud {user_input['calendar_name']}", data=data)

        # On redemande la liste pour l'afficher (rapide car on a déjà testé la connexion)
        calendar_names = await self.hass.async_add_executor_job(
            _test_connection_and_get_calendars,
            self._url,
            self._username,
            self._password,
        )

        return self.async_show_form(
            step_id="select_calendar",
            data_schema=vol.Schema(
                {
                    vol.Required("calendar_name"): vol.In(calendar_names),
                }
            ), # type: ignore
        )