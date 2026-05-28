# ANES CDF Codebook Excerpt — Core-Panel Variables

Extracted from the full variable codebook for the methodology's candidate items. This is the authoritative reference for codes, valid values, missing-value codes, and per-year coverage. If a needed variable is not here, consult the full codebook PDF/HTML.

**Direction target:** every item recoded so higher = more conservative on its axis. The 'intended' note below is a hypothesis — verify against the Valid codes shown.

## Coverage summary (study years present in 1980–2024)

The window contains 18 biennial study years: 1980, 1982, … 2024 (note: no 2006; 2008 present, no 2010/2014/2018/2022 in this CDF series — confirm against your data file).

| Variable | Axis | Yrs in window | Notes for panel selection |
|---|---|---|---|
| VCF0803 lib-con self-placement | economic | 18 | full coverage — anchor item |
| VCF0809 guaranteed jobs/income | economic | 17 | near-full — strong core |
| VCF0839 govt services-spending | economic | 16 | starts 1982 — strong core (REVERSE direction) |
| VCF0806 govt health insurance | economic | 12 | gaps; biennial-sparse |
| VCF0894 federal spending: welfare | economic? | 11 | 1992+ only |
| VCF0838 abortion (by law) | cultural | 17 | near-full — strong core (REVERSE direction) |
| VCF0830 aid to blacks | cultural | 16 | full-ish — strong core; watch form A/B wording break |
| VCF0853 traditional values emphasis | cultural | 14 | 1986+ — moral-traditionalism battery |
| VCF0852 adjust moral views | cultural | 14 | 1986+ — same battery |
| VCF0834 women equal role | cultural | 12 | gaps (missing 1986) |
| VCF0879a immigration (4-cat) | cultural? | 11 | 1992+ — too sparse early |
| VCF0876 protect homosexuals | cultural? | 10 | 1988+, intermittent |
| VCF9247 child-rearing (authoritarianism) | cultural? | 8 | 1992+, sparse — fails the rule |

**Implied fixed core panel (present in essentially all 18 window years):**
- Economic: VCF0803, VCF0809, VCF0839 (3 items; add VCF0806 only if you accept its 12-year gaps via imputation).
- Cultural: VCF0838, VCF0830 (2 items; VCF0834 has a 1986 gap; the moral-traditionalism pair VCF0852/0853 starts 1986, so usable only if you trim the window to 1986–2024).

Trade-off to decide: a **1980-start window** gives ~3 economic + 2 cultural fixed items. A **1986-start window** lets you add the moral-traditionalism battery and is more balanced on the cultural axis. For engine validation, balance across the two axes matters more than the two extra early years — leaning 1986–2024 is defensible. Confirm all coverage against the actual data file before committing.

---


## VCF0004 — YEAR OF STUDY
*Axis:* admin  |  *Coverage:* see Sources (none parsed)
*Intended use:* Year of study. Filter 1980-2024.


## VCF0301 — PARTY IDENTIFICATION OF RESPONDENT- 7-POINT SCALE
*Axis:* admin  |  *Coverage:* 1952–2024 | 18 study years in 1980–2024 window
*Intended use:* Party ID 7pt. Collapse to 3-cat Dem/Ind/Rep for party clouds.

**Valid codes:** 1. Strong Democrat 2. Weak Democrat 3. Independent - Democrat 4. Independent - Independent 5. Independent - Republican 6. Weak Republican 7. Strong Republican
**Missing codes:** 0. NA/RF initial party identification; Democrat or Republican initial party identification but DK/NA/RF strength; initial party identification independent/no preference/other/DK and followup is DK/NA/RF/other; no Pre IW INAP. question not used
**Study years fielded (from Sources):** 1952, 1956, 1958, 1960, 1962, 1964, 1966, 1968, 1970, 1972, 1974, 1976, 1978, 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: This variable has been revised in accordance with the ANES memo on construction of the Party Identification Summary (available from the ANES Web site). For all years, this variable has been reconstructed in the following consistent manner: Code 1: initial mention Democrat; followup: strong. Code 2: initial mention Democrat; followup: not strong. Code 3: initial preference independent,no preference, other, DK ; followup: Democrat Code 4: initial preference independent,no preference, […]

## VCF0009x — WEIGHT: FOR 1970 TYPE 0; 2012, 2016, 2024 FTF SAMPLE
*Axis:* admin  |  *Coverage:* 1958–2024 | 11 study years in 1980–2024 window
*Intended use:* Weight (FTF sample). Verify which weight applies to your year range.

**Study years fielded (from Sources):** 1958, 1960, 1974, 1976, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2024
**In 1980–2024 window:** 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2024
**Notes:** GENERAL NOTE: See Appendix documentation: WEIGHTS IN THE CUMULATIVE DATA FILE

## VCF0009z — WEIGHT: FOR 1970 TYPE 0; 2012-2024 FULL SAMPLE
*Axis:* admin  |  *Coverage:* 1958–2024 | 12 study years in 1980–2024 window
*Intended use:* Weight (full sample, incl. 2012-2024). Likely the one for 1980-2024.

**Study years fielded (from Sources):** 1958, 1960, 1974, 1976, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See Appendix documentation: WEIGHTS IN THE CUMULATIVE DATA FILE

## VCF0803 — LIBERAL-CONSERVATIVE SCALE
*Axis:* economic  |  *Coverage:* 1972–2024 | 18 study years in 1980–2024 window
*Intended use:* 7pt lib-con self-placement. 1=lib..7=cons -> ALREADY higher=conservative.

**Valid codes:** 1. Extremely liberal 2. Liberal 3. Slightly liberal 4. Moderate, middle of the road 5. Slightly conservative 6. Conservative 7. Extremely conservative 9. DK; haven’t thought much about it
**Missing codes:** 0. NA; no Post IW; form III,IV (1972); R not administered 7pt scale series (2000) INAP. question not used
**Study years fielded (from Sources):** 1972, 1974, 1976, 1978, 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: For years 1984 and later, a follow-up ‘choice’ question was asked of respondents who replied ‘don’t know’ or ‘haven’t thought much’ to this question; except for years 1984, 1986 and 1990 this follow-up ‘choice’ question was also asked of respondents who answered ‘moderate.’ For these years, a final 3-category summary was constructed: the ‘choice’ question is found in VCF0824; the final 3-category summary is VCF0849. 2000 NOTE: This variable represents 7-point scale data from interv […]

## VCF0809 — GUARANTEED JOBS AND INCOME SCALE
*Axis:* economic  |  *Coverage:* 1972–2024 | 17 study years in 1980–2024 window
*Intended use:* Guaranteed jobs/income 7pt. 1=govt-action(lib)..7=self-reliance(cons) -> already higher=cons.

**Valid codes:** 1. Government see to job and good standard of living 2. 3. 4. 5. 6. 7. Government let each person get ahead on his own 9. DK; haven’t thought much about it
**Missing codes:** 0. NA; no Post IW; split versions: not asked (2008); form A (1986); telephone IW (2000) INAP. question not used
**Study years fielded (from Sources):** 1972, 1974, 1976, 1978, 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See also: VCF0808. 1972 NOTE: This question was asked in the pre for form I and in the post for form II (and IV). 2000 NOTE: This variable represents 7-point scale data from interviews conducted face-to-face. Respondents interviewed by telephone were asked a branching series and are not included here. 2008 NOTE: This question was administered to a random half sample of respondents using verion ‘OLD’; the remaining respondents were administered an alternative version (version ‘NEW’) […]

## VCF0806 — GOVERNMENT HEALTH INSURANCE SCALE
*Axis:* economic  |  *Coverage:* 1970–2024 | 12 study years in 1980–2024 window
*Intended use:* Govt health insurance 7pt. 1=govt-plan(lib)..7=private(cons) -> already higher=cons.

**Valid codes:** 1. Government insurance plan 2. 3. 4. 5. 6. 7. Private insurance plan 9. DK; haven’t thought much about it
**Missing codes:** 0. NA; split versions: not asked (2008); Form II (1972); no Post IW; telephone IW (1984: see VCF0015, 2000) INAP. question not used
**Study years fielded (from Sources):** 1970, 1972, 1976, 1978, 1984, 1988, 1992, 1994, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1984, 1988, 1992, 1994, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See also VCF0805. 2000 NOTE 1: This variable represents 7-point scale data from interviews conducted face-to-face. Respondents interviewed by telephone were asked a branching series and are not included. 2000 NOTE 2: Approximately half of the respondents were randomly selected to be administered this question with the introduction read with the endpoint options in reverse order [private option first] and the endpoint labels in the respondent booklet reversed. 2008 NOTE: This questi […]

## VCF0839 — GOVERNMENT SERVICES-SPENDING SCALE
*Axis:* economic  |  *Coverage:* 1982–2024 | 16 study years in 1980–2024 window
*Intended use:* Govt services-spending 7pt. 1=fewer/cut(cons)..7=more(lib) -> REVERSE so higher=cons.

**Valid codes:** 1. Government should provide many fewer services: reduce spending a lot 2. 3. 4. 5. 6. 7. Government should provide many more services: increase spending a lot 9. DK; haven’t thought much about it
**Missing codes:** 0.NA; telephone IW (2000); split versions: not asked (2008) INAP. question not used
**Study years fielded (from Sources):** 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** 1980 NOTE: The 1980 version of this question was not comparable. 2000 NOTE: This variable represents 7-point scale data from interviews conducted face-to-face. Respondents interviewed by telephone were asked a branching series and are not represented here. 2004 NOTE: Tbis question was asked in the pre-election survey and the post- election survey. The pre-election data are reported here. 2008 NOTE: This question was administered to a random half sample of respondents using verion ‘OLD’; the rema […]

## VCF0894 — FEDERAL SPENDING- WELFARE PROGRAMS
*Axis:* economic?  |  *Coverage:* 1992–2024 | 11 study years in 1980–2024 window
*Intended use:* Federal spending: welfare. Check coverage/direction.

**Valid codes:** 1. Increased 2. Same 3. Decreased (before 2012: or cut out entirely) 8. DK
**Missing codes:** 9. NA; no Post IW; abbrev. telephone IW (1984) INAP. question not used
**Study years fielded (from Sources):** 1992, 1994, 1996, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1992, 1994, 1996, 2000, 2002, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See federal spending question text and notes for, and preceding, VCF0886.

## VCF0834 — WOMEN EQUAL ROLE SCALE
*Axis:* cultural  |  *Coverage:* 1972–2008 | 12 study years in 1980–2024 window
*Intended use:* Women equal role 7pt. 1=equal(lib)..7=home(cons) -> already higher=cons.

**Valid codes:** 1. Women and men should have an equal role 2. 3. 4. 5. 6. 7. Women’s place is in the home 9. DK; haven’t thought much about it
**Missing codes:** 0. NA; telephone IW (2000); split versions: not asked (2008) INAP. question not used
**Study years fielded (from Sources):** 1972, 1974, 1976, 1978, 1980, 1982, 1984, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008
**In 1980–2024 window:** 1980, 1982, 1984, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008
**Notes:** 2000 NOTE 1: This variable represents 7-point scale data from interviews conducted face-to-face; telephone respondents were administered a branching series and are not represented here. 2000 NOTE 2: Respondents were randomly selected to be administered this question with or without the option ‘or haven’t you thought much about this?’ read as part of the question text. Data for face-to- face respondents administered either version are represented in this variable. 2008 NOTE: This question was adm […]

## VCF0838 — BY LAW, WHEN SHOULD ABORTION BE ALLOWED
*Axis:* cultural  |  *Coverage:* 1980–2024 | 17 study years in 1980–2024 window
*Intended use:* Abortion 4pt by-law. 1=never..4=always-personal-choice -> REVERSE so higher=cons(restrictive).

**Valid codes:** 1. By law, abortion should never be permitted. 2. The law should permit abortion only in case of rape, incest, or when the woman’s life is in danger. 3. The law should permit abortion for reasons other than rape, incest, or danger to the woman’s life, but only after the need for the abortion has been clearly established. 4. By law, a woman should always be able to obtain an abortion as a matter of personal choice. 9. DK; other
**Missing codes:** 0. NA; no Post IW; split versions: not asked (2008); INAP. question not used
**Study years fielded (from Sources):** 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See also VCF0837. 1980 NOTE: Asked pre-election. Alternate version (ssee VCF0837) asked post-election. 2008 NOTE: This question was administered to a random half sample of respondents using verion ‘OLD’; the remaining respondents (version ‘NEW’) were administered a branching series of questions on abortion. 2016 NOTE: For Web cases, the Other option was not available.

## VCF0830 — AID TO BLACKS SCALE
*Axis:* cultural  |  *Coverage:* 1970–2024 | 16 study years in 1980–2024 window
*Intended use:* Aid to blacks 7pt. 1=govt-help(lib)..7=self-help(cons) -> already higher=cons; verify continuity.

**Valid codes:** 1. Government should help minority groups/blacks 2. 3. 4. 5. 6. 7. Minority groups/ blacks should help themselves 9. DK; haven’t thought much about it
**Missing codes:** 0. NA; telephone IW (2000); no Post IW INAP. question not used
**Study years fielded (from Sources):** 1970, 1972, 1974, 1976, 1978, 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2016, 2020, 2024
**In 1980–2024 window:** 1980, 1982, 1984, 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2016, 2020, 2024
**Notes:** GENERAL NOTE: Note that form B in 1986, form B in 1988, and all previous years specified ‘blacks and other minorities’ in this question, while form A in 1986, form A in 1988, and all cases in 1990 and after specified only ‘blacks.’ To filter for form A/B responses, use variable VCF0012. 2000 NOTE: This variable represents 7-point scale data from interviews conducted face-to-face; telephone respondents were administered asked a branching series and are not represented here.

## VCF0853 — SHOULD BE MORE EMPHASIS ON TRADITIONAL VALUES
*Axis:* cultural  |  *Coverage:* 1986–2024 | 14 study years in 1980–2024 window
*Intended use:* More emphasis on traditional values. Likely good 1986+ coverage; check direction.

**Valid codes:** 1. Agree strongly 2. Agree somewhat 3. Neither agree nor disagree 4. Disagree somewhat 5. Disagree strongly 8. DK
**Missing codes:** 9. NA; Form B (1990); no Post IW INAP. question not used
**Study years fielded (from Sources):** 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See VCF0851.

## VCF0852 — SHOULD ADJUST VIEW OF MORAL BEHAVIOR TO CHANGES
*Axis:* cultural  |  *Coverage:* 1986–2024 | 14 study years in 1980–2024 window
*Intended use:* Adjust view of moral behavior to changes. Moral-traditionalism battery; check direction.

**Valid codes:** 1. Agree strongly 2. Agree somewhat 3. Neither agree nor disagree 4. Disagree somewhat 5. Disagree strongly 8. DK
**Missing codes:** 9. NA; Form B (1990); no Post IW INAP. question not used
**Study years fielded (from Sources):** 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1986, 1988, 1990, 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** GENERAL NOTE: See VCF0851.

## VCF0879a — INCREASE OR DECREASE NUMBER OF IMMIGRANTS TO U.S. 4-CATEGORY
*Axis:* cultural?  |  *Coverage:* 1992–2024 | 11 study years in 1980–2024 window
*Intended use:* Immigration 4-category (increase/decrease). Sparse pre-2008 - check coverage.

**Valid codes:** 1. Increased 3. Same as now 5. Decreased 8. DK
**Missing codes:** 9. NA; no Post IW INAP. question not used
**Study years fielded (from Sources):** 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1992, 1994, 1996, 1998, 2000, 2004, 2008, 2012, 2016, 2020, 2024

## VCF0876 — LAW TO PROTECT HOMOSEXUALS AGAINST DISCRIMINATION
*Axis:* cultural?  |  *Coverage:* 1988–2024 | 10 study years in 1980–2024 window
*Intended use:* Law to protect homosexuals from discrimination. ~1988+, intermittent.

**Valid codes:** 1. Favor 5. Oppose 8. DK; depends (1988)
**Missing codes:** 9. NA; no Post IW INAP. question not used
**Study years fielded (from Sources):** 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**Notes:** 1988 NOTE: ‘Depends’ was a coding option in 1988 only. 2012 NOTE: This question was asked of a random 1/2 sample of respondents (the remaining 1/2 sample was asked a different version of the question).

## VCF9247 — WHICH IS MORE IMPORTANT FOR A CHILD TO HAVE: OBEDIENCE OR SELF-RELIANCE
*Axis:* cultural?  |  *Coverage:* 1992–2024 | 8 study years in 1980–2024 window
*Intended use:* Child-rearing: obedience vs self-reliance (authoritarianism battery). Recent only - check coverage.

**Valid codes:** 1. Obedience 2. Both (VOL) 3. Self-reliance 4. Neither (2020)
**Missing codes:** -8. DK -9. RF; NA; short questionnaire (1992); no post data INAP. Inap. question not used
**Study years fielded (from Sources):** 1992, 2000, 2004, 2008, 2012, 2016, 2020, 2024
**In 1980–2024 window:** 1992, 2000, 2004, 2008, 2012, 2016, 2020, 2024
