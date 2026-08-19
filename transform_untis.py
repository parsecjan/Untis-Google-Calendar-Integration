#!/usr/bin/env python3
"""Holt Jannis' persoenlichen Untis-Stundenplan direkt ueber die Untis-API
(kein iCal-Abo noetig) und veroeffentlicht ihn als datensparsamen Feed:
pro Tag nur EIN Block "In der Schule". Keine Faecher, Raeume, Freistunden."""

import os
from collections import defaultdict
from datetime import date, timedelta

import webuntis
from icalendar import Calendar, Event

# ---- Zugangsdaten aus Umgebungsvariablen (nie im Code!) ----
SERVER = os.environ["WEBUNTIS_SERVER"]     # z.B. "johnny.webuntis.com"
SCHOOL = os.environ["WEBUNTIS_SCHOOL"]     # z.B. "johnny"
USERNAME = os.environ["WEBUNTIS_USER"]     # dein Web-Login-Benutzer
PASSWORD = os.environ["WEBUNTIS_PASSWORD"] # dein Web-Login-Passwort

OUTPUT_FILE = "schule.ics"
BLOCK_TITLE = "In der Schule"
DAYS_BACK = 7
DAYS_AHEAD = 84            # ~12 Wochen im Voraus


def fetch_periods():
    start = date.today() - timedelta(days=DAYS_BACK)
    end = date.today() + timedelta(days=DAYS_AHEAD)
    with webuntis.Session(
        server=SERVER,
        school=SCHOOL,
        username=USERNAME,
        password=PASSWORD,
        useragent="LifeOS-Kalender",
    ).login() as s:
        return list(s.my_timetable(start=start, end=end))


def build_blocks(periods):
    lessons = defaultdict(list)   # Tag -> [(start, ende)]
    for p in periods:
        if getattr(p, "code", None) == "cancelled":
            continue              # entfallene Stunden ignorieren
        lessons[p.start.date()].append((p.start, p.end))

    out = Calendar()
    out.add("prodid", "-//Jannis//Schul-Verfuegbarkeit//DE")
    out.add("version", "2.0")
    out.add("x-wr-calname", "Jannis - Schule")
    out.add("color", "turquoise")                    # RFC 7986
    out.add("x-apple-calendar-color", "#1BADB8FF")   # Apple Vorfarbe

    for day, spans in sorted(lessons.items()):
        block_start = min(s for s, _ in spans)   # erste Stunde des Tages
        block_end = max(e for _, e in spans)     # letzte Stunde des Tages
        ev = Event()
        ev.add("summary", BLOCK_TITLE)
        ev.add("dtstart", block_start)
        ev.add("dtend", block_end)
        ev.add("uid", f"schule-{day.isoformat()}@jannis")
        ev.add("transp", "OPAQUE")   # wird als "belegt" angezeigt
        out.add_component(ev)
    return out


def main():
    periods = fetch_periods()
    out = build_blocks(periods)
    with open(OUTPUT_FILE, "wb") as f:
        f.write(out.to_ical())
    print(f"{OUTPUT_FILE} geschrieben ({len(out.subcomponents)} Bloecke).")


if __name__ == "__main__":
    main()
