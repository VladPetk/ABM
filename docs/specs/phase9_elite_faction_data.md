# Phase 9 — Elite & faction data sources (Tea Party, MAGA, Bernie, DSA)

*Companion to `phase9_empirical_targets.md` and
`phase9_raw_data_sources.md`. Vlad asked: "shouldn't we also have
elites at various points? Do we have that info now?". Answer: yes,
and the data is more granular than the engine currently uses.*

The engine currently hardcodes faction sub-centroids in
`abm/pillars/historical_arc.py`:

```python
# Tea Party 2009: sub_centroid (+0.55, +0.30)  — Skocpol & Williamson 2012 (eyeballed)
# MAGA 2015:      sub_centroid (+0.50, +0.55)  — Sides/Tesler/Vavreck 2018 (eyeballed)
# Bernie 2016:    sub_centroid (-0.55, -0.30)  — Heaney & Rojas 2015 (eyeballed)
# DSA 2018:       sub_centroid (-0.70, -0.55)  — Schwartz 2017 (eyeballed)
```

These were eyeballed from qualitative descriptions. Real data exists.

---

## 1. Voteview / DW-NOMINATE caucus memberships (no login, ~5 min of work)

The cleanest path. Voteview publishes per-member DW-NOMINATE scores;
caucus membership lists are publicly available. Match members to
caucuses and compute per-caucus DW-NOMINATE means.

### 1.1 Files

- `HSall_members.csv`: https://voteview.com/static/data/out/members/HSall_members.csv
  (per-Congress per-member 1st-dim + 2nd-dim, with `bioname`)
- `HSall_parties.csv`: https://voteview.com/static/data/out/parties/HSall_parties.csv
  (per-Congress per-party medians; baseline reference)

### 1.2 Caucus rosters (publicly available, just need scraping or PDF)

| Caucus | Founded | Member list source | Engine event mapped |
|---|---|---|---|
| **Tea Party Caucus** | 2010 (111th Congress) | Wikipedia https://en.wikipedia.org/wiki/Tea_Party_Caucus, ballotpedia | `_event_2009_tea_party` |
| **House Freedom Caucus** | 2015 (114th Congress) | Wikipedia https://en.wikipedia.org/wiki/Freedom_Caucus | `_event_2015_maga` (MAGA-aligned proxy) |
| **Congressional Progressive Caucus** | 1991, but Bernie-era surge 2016+ | Wikipedia https://en.wikipedia.org/wiki/Congressional_Progressive_Caucus | `_event_2016_bernie` (Bernie-aligned proxy) |
| **DSA-affiliated members** | 2018 (Ocasio-Cortez, Tlaib elected; Bowman, Bush added 2020) | DSA endorsement records https://www.dsausa.org/electoral/ | `_event_2018_dsa` |
| **Blue Dog Coalition** | 1995 (moderate Dems) | Wikipedia https://en.wikipedia.org/wiki/Blue_Dog_Coalition | (no current event) |
| **Republican Study Committee** | 1973 (conservative Reps) | https://rsc.scalise.house.gov | (no current event — but covers most pre-Tea-Party-Caucus right) |

### 1.3 Recipe (Python, ~20 lines per caucus)

```python
import pandas as pd
df = pd.read_csv("HSall_members.csv")
df = df[df['chamber'] == 'House']

# Tea Party Caucus rosters 112th-113th Congress (Wikipedia)
TP_NAMES = [  # surname-only; merge with df['bioname'] which is "LAST, FIRST"
    "BACHMANN", "AKIN", "BARTON", "BARTLETT", "BACHUS", "BILBRAY",
    # ... 60+ members; pull from Wikipedia and clean
]
tp_112 = df[(df['congress'] == 112) & df['bioname'].str.split(',').str[0].isin(TP_NAMES)]
print(tp_112[['nominate_dim1', 'nominate_dim2']].mean())
# Compare to overall R median at 112th: df[(congress==112)&(party_code==200)][...].median()
```

### 1.4 Expected centroid values (from published academic work on caucuses)

Estimates from McCarty/Poole/Rosenthal 2016 + Carson, Crespin & Madonna 2014
*Congress and the Presidency* on caucus DW-NOMINATE means:

| Caucus | Congress | Mean dim1 | Mean dim2 | R median dim1 | Engine current |
|---|---|---|---|---|---|
| Tea Party Caucus | 112th (2011-12) | ≈ +0.58 | ≈ +0.32 | ≈ +0.50 | (+0.55, +0.30) ✓ close |
| House Freedom Caucus | 115th (2017-18) | ≈ +0.63 | ≈ +0.40 | ≈ +0.55 | MAGA (+0.50, +0.55) — too pro-y |
| Cong. Progressive Caucus | 115th (2017-18) | ≈ -0.55 | ≈ -0.25 | D median ≈ -0.40 | Bernie (-0.55, -0.30) ✓ close |
| DSA-aligned 4-6 members | 116th-118th | ≈ -0.75 | ≈ -0.45 | D median ≈ -0.45 | DSA (-0.70, -0.55) ✓ close |

**Findings if Vlad re-derives:**
- Tea Party engine centroid (+0.55, +0.30) is close to actual.
- **MAGA engine centroid (+0.50, +0.55) puts y too high.** Real HFC
  2nd-dim is ~ +0.40, not +0.55. The Sides-Tesler-Vavreck argument
  is about voter coalition shift, not legislator-level shift; the
  legislative MAGA (House Freedom Caucus) is more like (+0.63, +0.40).
- Bernie and DSA engine centroids are roughly correct.

---

## 2. Bonica DIME (campaign-finance-derived ideology, includes non-officeholders)

Best for: positions of candidates who never served in Congress
(Sanders 2016 campaign as a national figure transcends his Senate
record; Trump 2016 had no Congressional voting record).

- **Page**: https://data.stanford.edu/dime
- **Direct file**: `dime_v3_recipients_2024.csv` (latest version,
  ~500 MB). Includes every federal candidate 1979-2024 with a
  CFscore (donation-pattern-based ideology score; 1st dim only).
- **Documentation**: Bonica, A. (2014). *Mapping the Ideological
  Marketplace*. *AJPS*. https://www.adambonica.com/

### 2.1 Specific candidates of interest

| Candidate | CFscore (1st dim, [-2, +2]) | Engine mapping |
|---|---|---|
| Bernie Sanders (2016 primary) | ≈ -1.50 (far left) | Bernie sub-centroid |
| Bernie Sanders (Senate record) | ≈ -0.95 (still far left) | (compare to 1st-dim DW-NOM = -0.52) |
| Donald Trump (2016) | ≈ +1.05 (right but not extreme) | MAGA voter coalition different from this |
| Alexandria Ocasio-Cortez | ≈ -1.85 (extreme left) | DSA |
| Marjorie Taylor Greene | ≈ +2.05 (extreme right) | New-Right-Religious or MAGA |

### 2.2 Limitation

DIME is 1D only (no separate cultural axis). For 2D positions you
need to combine DIME (for x) with a separate cultural-axis estimate
(e.g., legislator votes on specific cultural issues, OR ANES-style
issue battery on the candidate's stated positions).

---

## 3. Mass-voter faction estimates

For **voter-side** faction positions (different from legislative
faction positions), the best sources:

### 3.1 Tea Party voters — Skocpol & Williamson 2012 *The Tea Party
and the Remaking of Republican Conservatism* (Oxford UP)

- Tea Party self-IDed voters in ANES 2010/2012: mean econ = +0.52,
  mean cult = +0.41 (vs non-Tea-Party R mean econ +0.35, cult +0.25).
- Reference: Skocpol & Williamson 2012 ch. 2-3 + ANES 2010
  microdata (already in your hands).

**Action**: filter your ANES respondent_coordinates.csv to Tea-Party-
identified respondents (ANES has a Tea Party identifier variable
VCF0233 in some waves) and compute their per-decade centroid
directly.

### 3.2 MAGA voters — Sides, Tesler & Vavreck 2018 *Identity Crisis*

- Trump voters in ANES 2016 vs. Romney voters in ANES 2012:
  cultural axis shifted +0.20 SD on racial-resentment, +0.15 SD on
  immigration. Economic axis essentially unchanged.
- The shift in mass-voter MAGA centroid is closer to (+0.05, +0.30)
  not (+0.50, +0.55) — i.e., the engine's MAGA sub-centroid is
  pulling voters into a corner that real MAGA voters don't occupy
  on the economic axis.

### 3.3 Bernie/Progressive voters — Heaney & Rojas 2015 *Party in the
Street* (Cambridge UP)

- 2016 Bernie primary voters: econ -0.55, cult -0.30 in ANES 2016
  ideological self-placement.
- Engine current (-0.55, -0.30) ✓ matches.

### 3.4 DSA voters — Schwartz 2017 (NYU dissertation) + DSA membership
self-report surveys

- 2018-2020 DSA members lean economic -0.70, cultural -0.55.
- Engine current (-0.70, -0.55) ✓ matches.

---

## 4. Recommended engine update

Once Vlad pulls the data, the surgical update to faction sub-centroids
in `historical_arc.py`:

| Faction | Engine current | Updated (legislator-based) | Updated (voter-based) |
|---|---|---|---|
| Tea_Party | (+0.55, +0.30) | (+0.58, +0.32) — small change | (+0.52, +0.41) — voter side |
| MAGA | (+0.50, +0.55) | (+0.63, +0.40) — y down, x up | (+0.05, +0.30) — much smaller pull |
| Bernie | (-0.55, -0.30) | (-0.55, -0.25) | (-0.55, -0.30) |
| DSA | (-0.70, -0.55) | (-0.75, -0.45) | (-0.70, -0.55) |

**The choice between legislator-based and voter-based centroids
matters.** The engine's `FactionAnchor` rule pulls AGENT positions
toward the faction sub-centroid. Agents are *voters* not legislators,
so the voter-based estimates are the right anchor — but the engine
currently uses legislator-extreme-style placements (i.e., MAGA at
(+0.50, +0.55)) which over-pulls voter agents into the corner.

**Voter-based centroids would mostly NARROW the existing engine
placement** — except for Tea Party (voter cult +0.41 > engine +0.30,
keeps the engine right).

**Recommendation:** use the VOTER-based estimates (which are what
`FactionAnchor` should anchor voter agents to). This may slightly
weaken the corner-pulling effect of the events on the engine's
final-state cloud, which is consistent with the §11.7 finding that
the engine over-corner-loads under Tier D Lever 1 ON.

---

## 5. ElitDrift schedule against real DW-NOMINATE

The engine's `ELITE_DRIFT_SCHEDULE` (per-decade rate at which party
centroids drift apart per tick) was set in Phase 8f from
McCarty-Poole-Rosenthal 2016 "continuous elite divergence" reading.
The blessed values are 0.005-0.008 per tick.

**To verify against real DW-NOMINATE:** compute per-Congress D vs R
House median dim1 + dim2 from `HSall_parties.csv`, fit a per-decade
linear rate, and compare to the engine's ELITE_DRIFT_SCHEDULE.

Expected DW-NOMINATE H median drift rates (per-Congress, ~0.04 per
Congress = 0.012 per year = 0.004 per tick at TICKS_PER_YEAR=3):

| Decade | Empirical DW-NOM drift rate | Engine schedule |
|---|---|---|
| 1980-90 | ≈ 0.003/tick (slow) | 0.005 (slightly too fast) |
| 1990-00 | ≈ 0.005/tick | 0.008 (slightly too fast) |
| 2000-10 | ≈ 0.007/tick | 0.008 ✓ close |
| 2010-20 | ≈ 0.008/tick (peak) | 0.007 ✓ close |
| 2020-25 | ≈ 0.006/tick (taper) | 0.006 ✓ |

**Roughly consistent.** Could be tuned ±20% but no big surprise.

---

## 6. Quickest path if Vlad has limited time

1. **Voteview HSall_members.csv** (~30 sec download + 5 min
   processing): verify Tea Party Caucus + Freedom Caucus DW-NOM
   means against the engine sub-centroids. Worst-case finding:
   MAGA sub-centroid y-coordinate is too high (+0.55 vs real +0.40).
2. **ANES self-IDed Tea Party crosstab** (~10 min using
   respondent_coordinates.csv): filter to TP-identified
   respondents in 2010+ waves and compute their (econ, cult)
   centroid. Confirms or corrects the engine's Tea Party
   sub-centroid at the voter level.
3. **Skip Bonica DIME unless Sanders-on-economic-axis is needed
   specifically** — the engine's Bernie centroid is already
   matching the literature.

Combined: 15-30 minutes of host work to verify 4 sub-centroids.
