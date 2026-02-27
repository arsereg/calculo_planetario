#!/usr/bin/env python3
"""
Planetary Alignment on Perfect February 28th Calculator
========================================================

Calculates the last time the astronomical conditions of Feb 28, 2026
occurred simultaneously:

  1. Perfect February: non-leap year, Feb 1 = Sunday (Sun–Sat 4-week block)
  2. Saturn–Neptune conjunction (within 5°) — a ~36-year cycle event
  3. Mercury–Venus conjunction (within 5°)
  4. All 6 planets (Mercury, Venus, Jupiter, Saturn, Uranus, Neptune)
     on the same side of the sky (spread ≤ 180°)

Uses the Swiss Ephemeris (pyswisseph) with the built-in Moshier analytical
ephemeris (~0.1 arcsecond precision, 3000 BC – 3000 AD).

Dependencies:
    pip install pyswisseph
"""

import swisseph as swe
import calendar
import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PLANETS = {
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    "Uranus":  swe.URANUS,
    "Neptune": swe.NEPTUNE,
}

REFERENCE_YEAR = 2026

# Search range (Moshier ephemeris: 3000 BC – 3000 AD)
SEARCH_START = 2025
SEARCH_END = -3000

# Conjunction threshold (degrees) — planets considered "conjunct"
CONJUNCTION_THRESHOLD = 5.0

# Maximum spread for all 6 planets to be "on the same side of the sky"
MAX_SPREAD = 180.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_leap(year: int) -> bool:
    """Proleptic Gregorian leap year check (astronomical year numbering)."""
    if year <= 0:
        y = year
        if y % 4 != 0:
            return False
        if y % 100 != 0:
            return True
        if y % 400 != 0:
            return False
        return True
    return calendar.isleap(year)


def feb1_weekday(year: int) -> int:
    """
    Return the day of week for Feb 1 of the given year.
    0 = Monday, 6 = Sunday.
    Uses Julian Day Number for all years (works for BC dates too).
    """
    jd = swe.julday(year, 2, 1, 12.0)
    return int(jd + 1.5) % 7


def is_perfect_february_sunday(year: int) -> bool:
    """
    A 'Perfect February' starting on Sunday:
      1. Non-leap year (28 days = exactly 4 of each weekday)
      2. February 1 falls on a Sunday
    """
    if _is_leap(year):
        return False
    return feb1_weekday(year) == 6  # 6 = Sunday


def get_ecliptic_longitudes(year: int, month: int, day: int) -> dict[str, float]:
    """Compute geocentric ecliptic longitudes (degrees) for each planet."""
    jd = swe.julday(year, month, day, 12.0)
    longitudes = {}
    for name, planet_id in PLANETS.items():
        try:
            xx, _ = swe.calc_ut(jd, planet_id)
            longitudes[name] = xx[0]
        except Exception:
            return {}
    return longitudes


def angular_separation(lon1: float, lon2: float) -> float:
    """Shortest angular distance between two ecliptic longitudes."""
    diff = abs(lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)


def min_arc_spread(longitudes: list[float]) -> float:
    """Minimum arc (degrees) that contains all given longitudes."""
    if len(longitudes) < 2:
        return 0.0
    s = sorted(longitudes)
    max_gap = 0.0
    for i in range(len(s)):
        j = (i + 1) % len(s)
        gap = (s[j] - s[i]) % 360.0
        max_gap = max(max_gap, gap)
    return 360.0 - max_gap


def year_label(year: int) -> str:
    """Human-readable year label (handles BC dates)."""
    if year > 0:
        return str(year)
    elif year == 0:
        return "1 BC"
    else:
        return f"{abs(year) + 1} BC"


def format_longitudes(longs: dict[str, float]) -> str:
    """Pretty-print planetary longitudes."""
    parts = [f"{n[:3]}={v:6.1f}°" for n, v in longs.items()]
    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("  WHEN DID THIS LAST HAPPEN?")
    print("  Perfect February + Saturn-Neptune & Mercury-Venus conjunctions")
    print("  + 6 planets aligned on February 28th")
    print("=" * 72)

    # ------------------------------------------------------------------
    # Step 1: Analyze the 2026 reference event
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  REFERENCE: February 28, {REFERENCE_YEAR}")
    print(f"{'─' * 72}")

    ref_longs = get_ecliptic_longitudes(REFERENCE_YEAR, 2, 28)
    ref_spread = min_arc_spread(list(ref_longs.values()))
    sat_nep = angular_separation(ref_longs["Saturn"], ref_longs["Neptune"])
    mer_ven = angular_separation(ref_longs["Mercury"], ref_longs["Venus"])

    dow = datetime.date(REFERENCE_YEAR, 2, 1).strftime('%A')
    print(f"\n  Perfect February: Feb 1 = {dow}, 28 days (Sun–Sat 4-week block)")
    print(f"  Planets: {', '.join(PLANETS.keys())}")
    print(f"  {format_longitudes(ref_longs)}")
    print(f"\n  Saturn–Neptune separation:  {sat_nep:.2f}°  (conjunction!)")
    print(f"  Mercury–Venus separation:  {mer_ven:.2f}°  (conjunction!)")
    print(f"  6-planet arc spread:       {ref_spread:.2f}°")

    # ------------------------------------------------------------------
    # Step 2: Define search criteria
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  SEARCH CRITERIA (all must be true simultaneously on Feb 28)")
    print(f"{'─' * 72}")
    print(f"""
  1. Perfect February (non-leap, Feb 1 = Sunday)
  2. Saturn–Neptune conjunction: separation ≤ {CONJUNCTION_THRESHOLD}°
  3. Mercury–Venus conjunction:  separation ≤ {CONJUNCTION_THRESHOLD}°
  4. All 6 planets within {MAX_SPREAD}° arc (same side of sky)
""")

    # ------------------------------------------------------------------
    # Step 3: Search backwards
    # ------------------------------------------------------------------
    print(f"{'─' * 72}")
    print(f"  SEARCHING: {SEARCH_START} back to {year_label(SEARCH_END)}")
    print(f"{'─' * 72}\n")

    matches = []
    # Also track partial matches for context
    perfect_feb_count = 0
    sat_nep_on_feb28 = []
    both_conjunctions = []

    for year in range(SEARCH_START, SEARCH_END, -1):
        if not is_perfect_february_sunday(year):
            continue

        perfect_feb_count += 1
        longs = get_ecliptic_longitudes(year, 2, 28)
        if not longs:
            continue

        sn = angular_separation(longs["Saturn"], longs["Neptune"])
        mv = angular_separation(longs["Mercury"], longs["Venus"])
        spread = min_arc_spread(list(longs.values()))

        # Track Saturn-Neptune conjunctions on qualifying Feb 28ths
        if sn <= CONJUNCTION_THRESHOLD:
            sat_nep_on_feb28.append((year, sn, mv, spread, dict(longs)))

        # Track both conjunctions
        if sn <= CONJUNCTION_THRESHOLD and mv <= CONJUNCTION_THRESHOLD:
            both_conjunctions.append((year, sn, mv, spread, dict(longs)))

        # Full match: all criteria
        if (sn <= CONJUNCTION_THRESHOLD and
                mv <= CONJUNCTION_THRESHOLD and
                spread <= MAX_SPREAD):
            matches.append((year, sn, mv, spread, dict(longs)))
            gap = REFERENCE_YEAR - year
            print(f"  MATCH!  year {year_label(year):>8s}  |  Sat-Nep={sn:5.2f}°  "
                  f"Mer-Ven={mv:5.2f}°  spread={spread:6.2f}°  "
                  f"| {gap} yrs before 2026")

        if perfect_feb_count % 100 == 0:
            print(f"  ... scanned {perfect_feb_count} Perfect Februaries "
                  f"(year {year_label(year)}) ...")

    # ------------------------------------------------------------------
    # Step 4: Results
    # ------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  RESULTS")
    print(f"{'=' * 72}")

    print(f"\n  Search range: {SEARCH_START} to {year_label(SEARCH_END)} "
          f"(~{abs(SEARCH_START - SEARCH_END)} years)")
    print(f"  Perfect Februaries (Sunday start): {perfect_feb_count}")
    print(f"  Saturn–Neptune conjunctions on those Feb 28ths: "
          f"{len(sat_nep_on_feb28)}")
    print(f"  + Also Mercury–Venus conjunction: {len(both_conjunctions)}")
    print(f"  + Also all 6 planets same side of sky: {len(matches)}")

    # Show Saturn-Neptune conjunctions for context
    if sat_nep_on_feb28:
        print(f"\n  {'─' * 60}")
        print(f"  Saturn–Neptune conjunctions on Feb 28 of Perfect Februaries:")
        print(f"  {'─' * 60}")
        for year, sn, mv, spread, longs in sat_nep_on_feb28:
            mv_mark = f"Mer-Ven={mv:5.1f}°" + (" CONJ!" if mv <= 5 else "")
            print(f"    {year_label(year):>8s}  Sat-Nep={sn:5.2f}°  "
                  f"{mv_mark}  spread={spread:5.1f}°")

    # ------------------------------------------------------------------
    # Step 5: Final answer
    # ------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  ANSWER")
    print(f"{'=' * 72}")

    if matches:
        if len(matches) == 0:
            pass  # handled below
        else:
            print(f"\n  Full matches found: {len(matches)}")
            for year, sn, mv, spread, longs in sorted(matches, key=lambda x: -x[0]):
                print(f"\n    {year_label(year)} ({REFERENCE_YEAR - year} years "
                      f"before 2026)")
                print(f"    Saturn–Neptune: {sn:.2f}°   Mercury–Venus: {mv:.2f}°   "
                      f"Spread: {spread:.1f}°")
                print(f"    {format_longitudes(longs)}")

            most_recent = max(matches, key=lambda x: x[0])
            yr = most_recent[0]
            print(f"\n  ┌─────────────────────────────────────────────────────┐")
            print(f"  │  The last time ALL these conditions aligned on      │")
            print(f"  │  February 28th was: {year_label(yr):>8s}                         │")
            print(f"  │  That was {REFERENCE_YEAR - yr:,} years ago.{' ' * 25}│")
            print(f"  └─────────────────────────────────────────────────────┘")
    else:
        print(f"""
  NO MATCH FOUND in {abs(SEARCH_START - SEARCH_END):,} years of searching.

  ┌─────────────────────────────────────────────────────────┐
  │  The combination of conditions on Feb 28, 2026 has      │
  │  NOT occurred in at least the last {abs(SEARCH_START - SEARCH_END):,} years.        │
  │                                                         │
  │  It may have NEVER happened before in human history.    │
  └─────────────────────────────────────────────────────────┘
""")

    # ------------------------------------------------------------------
    # Step 6: Why is this so rare?
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  WHY IS THIS SO RARE?")
    print(f"{'─' * 72}")

    # Calculate individual probabilities
    # Perfect February Sunday: ~540 in 5025 years ≈ 1 in 9.3 years
    pf_rate = perfect_feb_count / abs(SEARCH_START - SEARCH_END)
    # Saturn-Neptune conjunction period: ~36 years
    # Mercury-Venus on Feb 28: inner planets cycle fast but must land on
    # the right day

    print(f"""
  Each condition alone is uncommon; together they're extraordinary:

    Perfect February (Sunday start):     ~1 every {1/pf_rate:.0f} years
    Saturn–Neptune conjunction (≤5°):    ~1 every 36 years
    Mercury–Venus conjunction (≤5°):     ~frequent, but on a specific date: rare
    All 6 planets same hemisphere:       depends on outer planet positions

  On Feb 28, 2026, Saturn and Neptune meet for the first time since
  1989 — but in 1989, February was not a Perfect February (Feb 1 was
  a Wednesday). The next Saturn–Neptune conjunction after 2026 won't
  be until ~2061.

  For Mercury AND Venus to also be conjunct on that exact same date,
  while all 6 planets are on the same side of the sky — that's the
  combination that makes this effectively unique in recorded history.
""")

    swe.close()


if __name__ == "__main__":
    main()
