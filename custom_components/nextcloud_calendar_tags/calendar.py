"""Plateforme Calendrier pour Nextcloud Calendar Tags."""
from __future__ import annotations

import logging
import datetime
import caldav
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = datetime.timedelta(minutes=15)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    config_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([NextcloudCalendarEntity(config_data)], True)


class NextcloudCalendarEntity(CalendarEntity):
    def __init__(self, config_data: dict) -> None:
        self._url = config_data["url"]
        self._username = config_data["username"]
        self._password = config_data["password"]
        self._calendar_name = config_data["calendar_name"] # <-- Le calendrier choisi
        self._name = f"Nextcloud {self._calendar_name}"
        self._event = None
        self._attr_unique_id = f"{DOMAIN}_{self._username}_{self._calendar_name}"
        self._cache: dict[tuple[datetime.datetime, datetime.datetime], list[CalendarEvent]] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def event(self) -> CalendarEvent | None:
        return self._event

    async def async_update(self) -> None:
        now = dt_util.now()
        start_of_day = dt_util.start_of_local_day(now)
        end_of_day = start_of_day + datetime.timedelta(days=1)
        
        events = await self.async_get_events(self.hass, start_of_day, end_of_day)
        
        if events:
            future_events = [e for e in events if e.end > now]
            if future_events:
                future_events.sort(key=lambda e: e.start)
                self._event = future_events[0]
                return
        self._event = None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list[CalendarEvent]:
        
        cache_key = (start_date, end_date)
        if cache_key in self._cache:
            return self._cache[cache_key]

        def _fetch_events():
            client = None
            events_list = []
            try:
                client = caldav.DAVClient(
                    url=self._url,
                    username=self._username,
                    password=self._password,
                    ssl_verify_cert=False,
                ) # type: ignore
                principal = client.principal()
                calendars = principal.calendars()
                
                # --- RECHERCHE DU BON CALENDRIER ---
                calendar = None
                for cal in calendars:
                    if cal.name == self._calendar_name:
                        calendar = cal
                        break
                
                if not calendar:
                    _LOGGER.error("Calendrier '%s' introuvable sur le serveur !", self._calendar_name)
                    return []
                
                _LOGGER.debug("Interrogation du calendrier : %s", calendar.name)
                results = calendar.search(
                    start=start_date, end=end_date, event=True, expand=False
                )

                for ev in results:
                    try:
                        comp = ev.icalendar_component
                        start = comp.get("dtstart")
                        end = comp.get("dtend") or start
                        if start is None:
                            continue

                        if isinstance(start.dt, datetime.date) and not isinstance(start.dt, datetime.datetime):
                            start_dt = dt_util.start_of_local_day(start.dt)
                            end_dt = dt_util.start_of_local_day(end.dt) + datetime.timedelta(days=1)
                        else:
                            start_dt = start.dt
                            end_dt = end.dt

                        summary = str(comp.get("summary") or "Sans titre")
                        description = str(comp.get("description") or "")
                        location = str(comp.get("location") or "")

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

                        events_list.append(CalendarEvent(
                            start=start_dt,
                            end=end_dt,
                            summary=summary,
                            description=final_description,
                            location=location,
                        ))
                    except Exception as ev_error:
                        _LOGGER.error("Erreur sur un événement : %s", ev_error)
            except Exception as e:
                _LOGGER.error("Erreur de connexion Nextcloud : %s", e)
            finally:
                if client:
                    client.close()
            return events_list

        events = await hass.async_add_executor_job(_fetch_events)

        if len(self._cache) > 5:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = events

        return events