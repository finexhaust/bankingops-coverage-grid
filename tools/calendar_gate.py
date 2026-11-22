"""Validation for dated sample events against published business calendars."""
from __future__ import annotations

from datetime import date
from typing import Any


def _iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def validate_calendar_data(data: object) -> list[str]:
    """Return structural errors in the sourced calendar reference data."""
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema") != "bocg.business-calendars.v1":
        return ["calendar reference has an unknown schema"]
    calendars = data.get("calendars")
    if not isinstance(calendars, dict) or not calendars:
        return ["calendar reference has no calendars"]
    for name, calendar in calendars.items():
        label = f"calendar {name!r}"
        if not isinstance(calendar, dict):
            errors.append(f"{label} is not an object")
            continue
        if not isinstance(calendar.get("source"), str) or not calendar["source"].strip():
            errors.append(f"{label} has no source")
        source_url = calendar.get("source_url")
        if source_url is not None and (
            not isinstance(source_url, str) or not source_url.startswith("https://")
        ):
            errors.append(f"{label} has an invalid source_url")
        years = calendar.get("coverage_years")
        if (
            not isinstance(years, list)
            or any(type(year) is not int or year < 1 for year in years)
            or len(years) != len(set(years))
        ):
            errors.append(f"{label} has invalid coverage_years")
            years = []
        weekend_days = calendar.get("weekend_days")
        if (
            not isinstance(weekend_days, list)
            or any(type(day) is not int or day not in range(1, 8) for day in weekend_days)
            or len(weekend_days) != len(set(weekend_days))
        ):
            errors.append(f"{label} has invalid weekend_days")
        holidays = calendar.get("holidays")
        if not isinstance(holidays, list):
            errors.append(f"{label} has invalid holidays")
            continue
        seen_holidays: set[str] = set()
        for holiday in holidays:
            parsed = _iso_date(holiday)
            if parsed is None or holiday in seen_holidays:
                errors.append(f"{label} has an invalid or duplicate holiday {holiday!r}")
            else:
                if parsed.year not in years:
                    errors.append(f"{label} holiday {holiday} is outside its coverage_years")
                seen_holidays.add(holiday)
    return errors


def validate_dated_sample(sample: object, calendar_data: object) -> list[str]:
    """Validate all settlement and cutoff events in one published sample."""
    errors: list[str] = []
    if not isinstance(sample, dict):
        return ["sample is not an object"]
    calendars: dict[str, Any] = (
        calendar_data.get("calendars", {})
        if isinstance(calendar_data, dict) and isinstance(calendar_data.get("calendars"), dict)
        else {}
    )
    events = sample.get("dated_events")
    if not isinstance(events, list) or not events:
        return ["sample has no dated_events"]
    for index, event in enumerate(events):
        label = f"dated event {index}"
        if not isinstance(event, dict):
            errors.append(f"{label} is not an object")
            continue
        event_type = event.get("event_type")
        if not isinstance(event_type, str) or event_type not in {"settlement", "cutoff"}:
            errors.append(f"{label} has an unsupported event_type")
        event_date = _iso_date(event.get("date"))
        if event_date is None:
            errors.append(f"{label} has an invalid ISO date")
            continue
        calendar_ref = event.get("calendar_ref")
        if not isinstance(calendar_ref, str) or not calendar_ref.strip():
            errors.append(f"{label} has no calendar_ref")
            continue
        calendar = calendars.get(calendar_ref)
        if not isinstance(calendar, dict):
            errors.append(f"{label} refers to unknown calendar {calendar_ref!r}")
            continue
        years = calendar.get("coverage_years")
        if not isinstance(years, list) or event_date.year not in years:
            errors.append(f"{label} date {event_date} is outside {calendar_ref!r} coverage")
            continue
        status = event.get("status")
        if not isinstance(status, str) or status not in {"open", "closed"}:
            errors.append(f"{label} has an invalid status")
            continue
        if status == "open":
            weekend_days = calendar.get("weekend_days")
            holidays = calendar.get("holidays")
            if isinstance(weekend_days, list) and event_date.isoweekday() in weekend_days:
                errors.append(f"{label} marks weekend {event_date} open on {calendar_ref}")
            if isinstance(holidays, list) and event.get("date") in holidays:
                errors.append(f"{label} marks holiday {event_date} open on {calendar_ref}")
    return errors
