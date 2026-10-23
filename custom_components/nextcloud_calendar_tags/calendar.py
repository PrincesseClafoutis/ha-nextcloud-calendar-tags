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
    """Configurer la plateforme calendrier."""
    config_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NextcloudCalendarEntity(config_data)], True)


class NextcloudCalendarEntity(CalendarEntity):
    """Représentation d'un calendrier Nextcloud."""

    def __init__(self, config_data: dict) -> None:
        """Initialiser l'entité."""
        self._url = config_data["url"]
        self._username = config_data["username"]
        self._password = config_data["password"]
        self._name = "Nextcloud Princesse Clafoutis"
        self._event = None
        self._attr_unique_id = f"{DOMAIN}_{self._username}"

    @property
    def name(self) -> str:
        """Nom de l'entité."""
        return self._name

    @property
    def event(self) -> CalendarEvent | None:
        """Retourne l'événement actuel."""
        return self._event

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list[CalendarEvent]:
        """Récupérer les événements et extraire les tags (catégories)."""
        events = []
        try:
            client = caldav.DAVClient(url=self._url, username=self._username, password=self._password)
            principal = client.principal()
            calendars = principal.calendars()
            if not calendars:
                return []
            
            calendar = calendars[0] 
            
            results = calendar.search(start=start_date, end=end_date, event=True, expand=True)
            
            for ev in results:
                summary = ev.icalendar_component.get('summary', 'Sans titre')
                description = ev.icalendar_component.get('description', '')

                categories = ev.icalendar_component.get('categories', [])
                tags_str = ""
                if categories:
                    if isinstance(categories, list):
                        tags_str = ", ".join([str(c) for c in categories])
                    else:
                        tags_str = str(categories)

                if tags_str:
                    final_description = f"[TAGS: {tags_str}] {description}"
                else:
                    final_description = description

                event = CalendarEvent(
                    start=ev.icalendar_component.get('dtstart').dt,
                    end=ev.icalendar_component.get('dtend').dt,
                    summary=str(summary),
                    description=final_description,
                    location=str(ev.icalendar_component.get('location', '')),
                )
                events.append(event)
                
        except Exception as e:
            _LOGGER.error("Erreur lors de la récupération des événements Nextcloud : %s", e)

        return events