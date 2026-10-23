"""Plateforme Calendrier pour Nextcloud Calendar Tags."""
from __future__ import annotations

import logging
import datetime
import caldav
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer la plateforme calendrier à partir d'une entrée de config."""


    async_add_entities([NextcloudCalendarEntity(config_entry)], True)


class NextcloudCalendarEntity(CalendarEntity):
    """Représentation d'un calendrier Nextcloud avec tags."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialiser l'entité."""
        self.config_entry = config_entry
        self._name = "Nextcloud Princesse Clafoutis"
        self._event = None
        self._attr_unique_id = f"{DOMAIN}_{self._name}"

    @property
    def name(self) -> str:
        """Nom de l'entité."""
        return self._name

    @property
    def event(self) -> CalendarEvent | None:
        """Retourne l'événement actuel ou le prochain."""
        return self._event

    async def async_update(self) -> None:
        """Récupérer les événements depuis Nextcloud."""


        pass

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list[CalendarEvent]:
        """Récupérer les événements dans une plage de dates."""


        return []