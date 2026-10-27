"""Initialisation de l'intégration Nextcloud Calendar Tags."""
from __future__ import annotations

import logging
from importlib import import_module
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["calendar"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer l'intégration à partir d'une entrée de configuration."""
    try:
        client = caldav.DAVClient(
            url=entry.data["url"],
            username=entry.data["username"],
            password=entry.data["password"],
            ssl_verify_cert=False,  # <-- LA LIGNE À AJOUTER
        )
        await hass.async_add_executor_job(client.principal)
    except Exception as ex:
        _LOGGER.warning("Impossible de se connecter à Nextcloud : %s", ex)
        raise ConfigEntryNotReady(f"Impossible de se connecter à Nextcloud: {ex}") from ex

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok