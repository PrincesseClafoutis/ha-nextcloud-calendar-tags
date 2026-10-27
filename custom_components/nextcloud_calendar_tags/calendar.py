"""Plateforme Calendrier pour Nextcloud Calendar Tags."""
from __future__ import annotations

import logging
import datetime
import functools
import importlib
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

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
        self._name = "Nextcloud Laure"
        self._event = None
        self._attr_unique_id = f"{DOMAIN}_{self._username}"

    @property
    def name(self) -> str:
        """Nom de l'entité."""
        return self._name

    @property
    def event(self) -> CalendarEvent | None:
        """Retourne le prochain événement."""
        return self._event

    async def async_update(self) -> None:
        """Récupère le prochain événement pour mettre à jour l'état."""
        now = dt_util.now()
        events = await self.async_get_events(self.hass, now, now + datetime.timedelta(days=30))
        if events:
            events.sort(key=lambda e: e.start)
            self._event = events[0]
            _LOGGER.debug("Prochain événement trouvé : %s le %s", self._event.summary, self._event.start)
        else:
            self._event = None
            _LOGGER.debug("Aucun événement à venir trouvé dans les 30 prochains jours.")

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list[CalendarEvent]:
        """Récupérer les événements et extraire les tags (catégories)."""
        events = []
        try:
            caldav = importlib.import_module("caldav")
            client = caldav.DAVClient(
                url=self._url,
                username=self._username,
                password=self._password,
                ssl_verify_cert=False,
            )
            principal = await hass.async_add_executor_job(client.principal)
            calendars = await hass.async_add_executor_job(principal.calendars)
            if not calendars:
                _LOGGER.warning("Aucun calendrier trouvé sur le serveur Nextcloud.")
                return []

            calendar = calendars[0]
            results = await hass.async_add_executor_job(
                functools.partial(
                    calendar.search,
                    start=start_date,
                    end=end_date,
                    event=True,
                    expand=False,
                )
            )
            _LOGGER.debug("%s événements bruts reçus de Nextcloud.", len(results))

            for ev in results:
                try:
                    comp = ev.icalendar_component

                    start = comp.get("dtstart")
                    end = comp.get("dtend") or start

                    if start is None:
                        _LOGGER.warning("Événement sans date de début ignoré.")
                        continue

                    summary = comp.get("summary") or "Sans titre"
                    description = comp.get("description") or ""
                    location = comp.get("location") or ""

                    categories = comp.get("categories", [])
                    tags = []
                    if categories:
                        if isinstance(categories, list):
                            tags = [str(c) for c in categories]
                        else:
                            try:
                                tags = [str(c) for c in categories]
                            except Exception:
                                tags = [str(categories)]

                    if tags:
                        final_description = f"[TAGS: {', '.join(tags)}] {description}"
                    else:
                        final_description = description

                    if isinstance(start.dt, datetime.date) and not isinstance(start.dt, datetime.datetime):
                        event = CalendarEvent(
                            start=start.dt,
                            end=end.dt,
                            summary=str(summary),
                            description=final_description,
                            location=str(location),
                        )
                    else:
                        event = CalendarEvent(
                            start=start.dt,
                            end=end.dt,
                            summary=str(summary),
                            description=final_description,
                            location=str(location),
                        )
                    events.append(event)
                except Exception as ev_error:
                    _LOGGER.error("Erreur lors de l'analyse d'un événement : %s", ev_error)

        except Exception as e:
            _LOGGER.error("Erreur lors de la récupération des événements Nextcloud : %s", e)

        events.sort(key=lambda e: e.start)
        return events