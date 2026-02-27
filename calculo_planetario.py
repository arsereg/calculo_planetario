#!/usr/bin/env python3
"""
Planetary Alignment on Perfect February 28th Calculator
========================================================

Calculates the last time 6 planets (Mercury, Venus, Jupiter, Saturn, Uranus,
Neptune) were aligned on February 28th of a "Perfect February" — a February
with exactly 4 occurrences of each day of the week (28 days = non-leap year).

The February 28, 2026 event is used as the reference alignment.

Uses the Swiss Ephemeris (pyswisseph) with the built-in Moshier analytical
ephemeris, which provides ~0.1 arcsecond precision for dates between
3000 BC and 3000 AD — more than sufficient for alignment detection.

Dependencies:
    pip install pyswisseph
"""

import swisseph as swe
import calendar
import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The 6 planets in the Feb 28, 2026 alignment
# (Saturn, Mercury, Neptune, Venus, Uranus, Jupiter — NOT Mars)
PLANETS = {
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    "Uranus":  swe.URANUS,
    "Neptune": swe.NEPTUNE,
}

REFERENCE_YEAR = 2026

# Search range (Moshier ephemeris is reliable 3000 BC – 3000 AD)
SEARCH_START = 2025
SEARCH_END = -3000

# Gap (in years) that separates distinct "clusters" of matching years
CLUSTER_GAP = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_perfect_february(year: int) -> bool:
    """
    A 'Perfect February' has exactly 4 of each day of the week.
    4 x 7 = 28, so this requires February to have exactly 28 days → non-leap year.

    Uses proleptic Gregorian calendar for years <= 0.
    Astronomical year numbering: 1 BC = year 0, 2 BC = year -1, etc.
    """
    if year <= 0:
        y = year
        if y % 4 != 0:
            return True   # not leap → perfect
        if y % 100 != 0:
            return False  # leap
        if y % 400 != 0:
            return True   # not leap → perfect
        return False       # leap
    return not calendar.isleap(year)


def get_ecliptic_longitudes(year: int, month: int, day: int) -> dict[str, float]:
    """
    Compute geocentric ecliptic longitudes (degrees) for each planet.
    Uses Swiss Ephemeris Julian Day conversion and Moshier analytical ephemeris.
    """
    jd = swe.julday(year, month, day, 12.0)  # noon UT
    longitudes = {}
    for name, planet_id in PLANETS.items():
        try:
            xx, _ = swe.calc_ut(jd, planet_id)
            longitudes[name] = xx[0]
        except Exception:
            return {}
    return longitudes


def min_arc_spread(longitudes: list[float]) -> float:
    """
    Calculate the minimum arc (degrees) that contains all given longitudes.
    Handles the circular wrap-around at 0°/360°.
    """
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
    """Pretty-print planetary longitudes in a single line."""
    parts = [f"{n[:3]}={v:6.1f}°" for n, v in longs.items()]
    return "  ".join(parts)


def find_clusters(matches: list[tuple], gap_threshold: int) -> list[list[tuple]]:
    """
    Group matches into clusters: consecutive years within gap_threshold
    of each other belong to the same cluster.
    """
    if not matches:
        return []
    sorted_matches = sorted(matches, key=lambda x: x[0])
    clusters = [[sorted_matches[0]]]
    for m in sorted_matches[1:]:
        if m[0] - clusters[-1][-1][0] <= gap_threshold:
            clusters[-1].append(m)
        else:
            clusters.append([m])
    return clusters


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("  PLANETARY ALIGNMENT ON PERFECT FEBRUARY 28th")
    print("  When did 6 planets last align on Feb 28 of a Perfect February?")
    print("=" * 72)

    # ------------------------------------------------------------------
    # Step 1: Establish the 2026 reference
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  REFERENCE: February 28, {REFERENCE_YEAR}")
    print(f"{'─' * 72}")

    ref_longs = get_ecliptic_longitudes(REFERENCE_YEAR, 2, 28)
    ref_spread = min_arc_spread(list(ref_longs.values()))

    dow = datetime.date(REFERENCE_YEAR, 2, 1).strftime('%A')
    print(f"\n  Perfect February: Yes (non-leap, 28 days, Feb 1 = {dow})")
    print(f"  Planets: {', '.join(PLANETS.keys())}")
    print(f"  Longitudes: {format_longitudes(ref_longs)}")
    print(f"  Minimum arc spread: {ref_spread:.2f}°")

    threshold = ref_spread
    print(f"\n  Alignment threshold: spread <= {threshold:.2f}°")
    print(f"  (any 6-planet configuration as tight or tighter than 2026)")

    # ------------------------------------------------------------------
    # Step 2: Search backwards
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  SEARCHING: year {SEARCH_START} back to {year_label(SEARCH_END)}")
    print(f"  Conditions: non-leap year + 6-planet spread <= {threshold:.2f}°")
    print(f"{'─' * 72}\n")

    matches = []
    years_checked = 0

    for year in range(SEARCH_START, SEARCH_END, -1):
        if not is_perfect_february(year):
            continue

        years_checked += 1
        longs = get_ecliptic_longitudes(year, 2, 28)
        if not longs:
            continue

        spread = min_arc_spread(list(longs.values()))

        if spread <= threshold:
            matches.append((year, spread, dict(longs)))

        if years_checked % 500 == 0:
            print(f"  ... scanned to year {year_label(year)} "
                  f"({years_checked} candidates checked) ...")

    # ------------------------------------------------------------------
    # Step 3: Cluster analysis
    # ------------------------------------------------------------------
    clusters = find_clusters(matches, CLUSTER_GAP)

    print(f"\n{'=' * 72}")
    print(f"  RESULTS")
    print(f"{'=' * 72}")
    print(f"\n  Search range:           {SEARCH_START} to {year_label(SEARCH_END)}")
    print(f"  Non-leap years checked: {years_checked}")
    print(f"  Threshold:              <= {threshold:.2f}°")
    print(f"  Total matches:          {len(matches)}")
    print(f"  Distinct clusters:      {len(clusters)} "
          f"(grouped by {CLUSTER_GAP}-year gaps)")

    print(f"\n{'─' * 72}")
    print(f"  CLUSTER SUMMARY (each cluster is an 'era' of favorable alignment)")
    print(f"{'─' * 72}")

    for i, cluster in enumerate(reversed(clusters)):
        first_year = cluster[0][0]
        last_year = cluster[-1][0]
        best = min(cluster, key=lambda x: x[1])
        span = last_year - first_year
        years_before = REFERENCE_YEAR - last_year

        era_label = (f"{year_label(first_year)}"
                     + (f" – {year_label(last_year)}" if span > 0 else ""))

        marker = " ◀ CURRENT ERA" if last_year >= 1982 else ""
        print(f"\n  Cluster {i+1}: {era_label}  "
              f"({len(cluster)} matches over {span} yrs){marker}")
        print(f"    Best alignment: {year_label(best[0])} "
              f"(spread={best[1]:.1f}°)")
        if years_before > 0:
            print(f"    Distance from 2026: ~{years_before} years")

    # ------------------------------------------------------------------
    # Step 4: Identify the gap to the previous era
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  KEY FINDING")
    print(f"{'─' * 72}")

    # Find the cluster containing recent years and the one before it
    recent_cluster = None
    previous_cluster = None
    for i, cluster in enumerate(reversed(clusters)):
        last_yr = cluster[-1][0]
        if last_yr >= 1980 and recent_cluster is None:
            recent_cluster = cluster
        elif recent_cluster is not None and previous_cluster is None:
            previous_cluster = cluster
            break

    if recent_cluster and previous_cluster:
        rc_first = recent_cluster[0][0]
        rc_last = recent_cluster[-1][0]
        pc_first = previous_cluster[0][0]
        pc_last = previous_cluster[-1][0]
        gap_years = rc_first - pc_last

        print(f"\n  The 2026 alignment belongs to a cluster spanning "
              f"{year_label(rc_first)} – {year_label(rc_last)}")
        print(f"  ({len(recent_cluster)} qualifying Feb 28ths in this era)")
        print(f"\n  The PREVIOUS cluster of alignments was "
              f"{year_label(pc_first)} – {year_label(pc_last)}")
        print(f"  ({len(previous_cluster)} qualifying Feb 28ths)")
        print(f"\n  Gap between eras: ~{gap_years} years")
        print(f"  Last qualifying year from previous era: "
              f"{year_label(pc_last)} ({REFERENCE_YEAR - pc_last} years "
              f"before 2026)")

    # ------------------------------------------------------------------
    # Step 5: Multi-threshold analysis
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  SENSITIVITY ANALYSIS (how threshold affects rarity)")
    print(f"{'─' * 72}")

    for thr in [60, 80, 100, threshold, 140, 180]:
        count = sum(1 for _, s, _ in matches if s <= thr)
        sub_clusters = find_clusters(
            [(y, s, l) for y, s, l in matches if s <= thr], CLUSTER_GAP)
        label = " ◀ 2026 threshold" if thr == threshold else ""
        print(f"    <= {thr:6.1f}°: {count:>4d} matches, "
              f"{len(sub_clusters):>3d} clusters{label}")

    # ------------------------------------------------------------------
    # Step 6: The tightest alignments ever
    # ------------------------------------------------------------------
    print(f"\n{'─' * 72}")
    print(f"  TOP 10 TIGHTEST ALIGNMENTS (Feb 28, Perfect February, all time)")
    print(f"{'─' * 72}")

    top10 = sorted(matches, key=lambda x: x[1])[:10]
    for rank, (year, spread, longs) in enumerate(top10, 1):
        gap = REFERENCE_YEAR - year
        print(f"    #{rank:>2d}  {year_label(year):>8s}  spread={spread:5.1f}°  "
              f"({gap} yrs {'before' if gap > 0 else 'after'} 2026)")
        print(f"         {format_longitudes(longs)}")

    # ------------------------------------------------------------------
    # Step 7: Final answer
    # ------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  ANSWER")
    print(f"{'=' * 72}")

    if recent_cluster and previous_cluster:
        pc_last = previous_cluster[-1][0]
        all_best = min(matches, key=lambda x: x[1])
        print(f"""
  On Feb 28, 2026, six planets (Mercury, Venus, Jupiter, Saturn, Uranus,
  Neptune) will align within {ref_spread:.1f}° of ecliptic longitude during
  a Perfect February (28 days = 4 of each weekday).

  Using the 2026 spread ({ref_spread:.1f}°) as the alignment threshold:

    - The most recent PREVIOUS year meeting all conditions:
      {year_label(pc_last)} — approximately {REFERENCE_YEAR - pc_last} years ago

    - The current favorable era spans {year_label(rc_first)} – {year_label(rc_last)}
      ({len(recent_cluster)} qualifying years)

    - The previous favorable era was {year_label(pc_first)} – {year_label(pc_last)}
      ({len(previous_cluster)} qualifying years)

    - Gap between eras: ~{rc_first - pc_last} years

    - The tightest alignment in the searched {abs(SEARCH_START - SEARCH_END)}-year
      window was {year_label(all_best[0])} at just {all_best[1]:.1f}° spread

  This pattern is governed by Neptune (~165 yr orbit) and Uranus (~84 yr
  orbit). When these slow outer planets are on the same side of the ecliptic,
  the faster planets (Jupiter, Saturn, Mercury, Venus) periodically join
  them on Feb 28, creating clusters of alignments. Between favorable
  configurations of Neptune and Uranus, there are long gaps where no
  alignment is possible on February 28.
""")
    else:
        print("\n  Could not determine cluster structure from results.\n")

    swe.close()


if __name__ == "__main__":
    main()
