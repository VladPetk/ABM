/* affect-symptoms-data.js  ->  window.ANIMUS_DATA
 *
 * FAITHFUL, CITED empirical series on US affective polarization ("animus")
 * for the "thermometer + bars" visual. Hand-curated from primary sources
 * (ANES, Pew, PRRI, peer-reviewed). This file is NOT engine output -- it is
 * the external empirical reference layer. Every number carries a source+url.
 *
 * Honesty flags per series:
 *   solid       = published exact figure, consistent instrument
 *   snapshot    = single-year or few-year cross-section (not a smooth trend)
 *   wording_break = item wording/scale changed across waves; show as snapshots
 *   approx      = read off a figure / prose summary; value soft (+/- a few pts)
 *   gap         = no measured value at this date; do not invent / extrapolate only with a label
 *
 * Schema version 1. Years are calendar years. Values are in the stated unit.
 */
window.ANIMUS_DATA = {
  meta: {
    version: 1,
    title: "US affective polarization -- symptoms of partisan animus",
    note: "External empirical reference (ANES/Pew/PRRI/peer-reviewed). Pair with the polarlab engine `aff` series for the honest sim-vs-real overlay. ANES thermometer ('the [party]') and Pew thermometer ('Democrats/Republicans' as people) are DIFFERENT instruments -- keep on separate panels.",
    party_robustness_caveat: "Druckman & Levendusky / 2024 APSR letter: the thermometer may overstate animus toward ORDINARY out-partisans (respondents may picture politicians). The GAP TREND is robust; the LEVEL of 'hatred of ordinary voters' is contested. Footnote this on the spine."
  },

  /* ===== SPINE: ANES feeling thermometer, in-party vs out-party (0-100) ===== */
  thermometer: {
    id: "anes_thermometer",
    unit: "degrees (0-100)",
    flag: "solid (anchors) + approx (interpolated decades)",
    item: "ANES 0-100 feeling thermometer toward 'the Democratic/Republican Party' (partisan respondents), 1978-present.",
    headline: "In-party warmth ~flat near 70-76; out-party warmth collapses ~48 (1978) -> ~20s (2020s). Gap roughly doubles.",
    anchors_in_party:  [ {year:1980, v:71.7}, {year:1982, v:72.7}, {year:2020, v:75, flag:"approx"} ],
    anchors_out_party: [ {year:1978, v:48, flag:"approx"}, {year:1980, v:52.8}, {year:1982, v:49.0}, {year:2020, v:20, flag:"approx"} ],
    gap_anchors: [ {year:1978, v:27.4}, {year:2016, v:40.87}, {year:2020, v:56.3} ],
    slopes: { affective_polarization_per_decade: 5.6, out_party_affect_per_decade: -6.2, note:"Boxell/Gentzkow/Shapiro 2024: US steepest of 12 OECD nations; in-party ~flat. 1978 SD=26.7." },
    sources: [
      {label:"Iyengar, Sood & Lelkes 2012 (POQ), Table 1 -- 1980/1982 means", url:"https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-poq-affect-not-ideology.pdf"},
      {label:"Iyengar et al. 2019 (Annual Review Pol Sci) -- gap 22.64(1978)->40.87(2016)", url:"https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-ar-origins.pdf"},
      {label:"Boxell, Gentzkow & Shapiro 2024 (REStat / NBER w26669) -- slopes, gap 27.4->56.3", url:"https://web.stanford.edu/~gentzkow/research/cross-polar.pdf"},
      {label:"Finkel et al. 2020 (Science) -- in ~75 flat, out ~48->~20", url:"https://www.science.org/doi/10.1126/science.abe1715"}
    ]
  },

  /* ===== BARS: symptom series ===== */
  bars: [
    {
      id:"very_unfavorable", flag:"solid", unit:"% rating other party VERY unfavorable",
      label:"\"Very unfavorable\" view of the other party",
      why:"Cleanest long bar series, consistent Pew wording 1994-2022.",
      series:[ {year:1994, dem:16, rep:17, flag:"approx"}, {year:2000, dem:23, rep:26}, {year:2012, dem:43, rep:43, flag:"approx"}, {year:2016, dem:55, rep:58}, {year:2022, dem:54, rep:62} ],
      extra:{ both_parties_unfavorable:[{year:1994,v:6},{year:2022,v:27}] },
      sources:[ {label:"Pew 2016 'Partisanship and Political Animosity'", url:"https://www.pewresearch.org/politics/2016/06/22/1-feelings-about-partisans-and-the-parties/"},
                {label:"Pew 2022 'As Partisan Hostility Grows'", url:"https://www.pewresearch.org/politics/2022/08/09/as-partisan-hostility-grows-signs-of-frustration-with-the-two-party-system/"} ]
    },
    {
      id:"child_marriage", flag:"wording_break", unit:"% upset / displeased if child married out-party",
      label:"Unhappy if their child married someone from the other party",
      why:"The viral 'wow' stat. Show as 3 snapshots, not a line (wording/scale changed).",
      series:[ {year:1960, dem:4, rep:5, item:"pleased/displeased/no difference (Almond-Verba)"},
               {year:2008, dem:20, rep:27, item:"somewhat/very upset (YouGov)"},
               {year:2010, dem:33, rep:49, item:"somewhat/very unhappy (YouGov 11-nation)"} ],
      sources:[ {label:"Iyengar, Sood & Lelkes 2012 (POQ)", url:"https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-poq-affect-not-ideology.pdf"} ]
    },
    {
      id:"very_cold", flag:"solid", unit:"% rating other party 0-24 ('very cold') on thermometer",
      label:"\"Very cold\" toward the other party (0-24 of 100)",
      why:"Pairs with the thermometer line -- same instrument, shows the cold tail thickening.",
      series:[ {year:1964, dem:14, rep:10}, {year:2012, dem:50, rep:44} ],
      sources:[ {label:"Pew 2016 (citing ANES)", url:"https://www.pewresearch.org/politics/2016/06/22/1-feelings-about-partisans-and-the-parties/"} ]
    },
    {
      id:"afraid_threat", flag:"snapshot", unit:"% (2016)",
      label:"Other party makes me \"afraid\" / is a \"threat to the nation\"",
      why:"Visceral 2016 callout. Single-year, no long trend.",
      series:[ {year:2016, metric:"afraid", dem:55, rep:49}, {year:2016, metric:"threat_to_nation", dem:41, rep:45} ],
      extra:{ threat_dem_2014:31 },
      sources:[ {label:"Pew 2016 'Partisanship and Political Animosity'", url:"https://www.pewresearch.org/politics/2016/06/22/partisanship-and-political-animosity-in-2016/"} ]
    },
    {
      id:"more_immoral", flag:"solid", unit:"% saying other party more immoral",
      label:"The other party is \"more immoral\" than other Americans",
      why:"Best dated proxy for 'evil, not just wrong' (2016->2022).",
      series:[ {year:2016, dem:35, rep:47}, {year:2022, dem:63, rep:72} ],
      extra:{ more_dishonest_2022:{dem:64,rep:72}, more_closedminded_2022:{dem:83,rep:69} },
      sources:[ {label:"Pew 2022 'As Partisan Hostility Grows'", url:"https://www.pewresearch.org/politics/2022/08/09/as-partisan-hostility-grows-signs-of-frustration-with-the-two-party-system/"} ]
    },
    {
      id:"cross_party_marriage", flag:"solid (co-partisan) / method_break (D-R share)", unit:"%",
      label:"Cross-party marriage is vanishing",
      why:"Firmest long-run cross-party-TIE series; the model's `xc` analogue.",
      copartisan_spouse:[ {year:1973, v:54}, {year:2013, v:74} ],
      cross_party_married:[ {year:1973, v:46}, {year:2013, v:26} ],
      dem_rep_marriages:[ {year:2016, v:9, method:"voter file (Hersh & Ghitza)"}, {year:2020, v:3.6, method:"survey (IFS AFS)"} ],
      note:"9% (2016 voterfile) and 3.6% (2020 survey) use DIFFERENT methods -- not directly comparable. Within-method mixed-marriage decline 23%->21% (2017->2020).",
      sources:[ {label:"Iyengar, Konitzer & Tedin 2018 (J of Politics)", url:"https://pcl.sites.stanford.edu/sites/g/files/sbiybj22066/files/media/file/iyengar-moderating-effects.pdf"},
                {label:"IFS / Wang & Hersh-Ghitza", url:"https://ifstudies.org/blog/marriages-between-democrats-and-republicans-are-extremely-rare"} ]
    },
    {
      id:"siloed_media", flag:"snapshot", unit:"% of consistent partisans naming one main source",
      label:"Siloed news diets",
      why:"Cross-cutting-diet companion. 2014 snapshot.",
      series:[ {year:2014, group:"consistent_conservatives", source:"Fox News (main political-news source)", v:47},
               {year:2014, group:"consistent_liberals", source:"most-named (CNN)", v:15, note:"liberals dispersed: CNN 15, NPR 13, MSNBC 12 -- no dominant silo"} ],
      sources:[ {label:"Pew 2014 'Political Polarization & Media Habits'", url:"https://www.pewresearch.org/journalism/2014/10/21/political-polarization-media-habits/"} ]
    },
    {
      id:"friendship_networks", flag:"snapshot", unit:"%",
      label:"Politically homogeneous social networks",
      why:"Direct cross-party-tie snapshot (no 1980 baseline -- see gap).",
      series:[ {year:2013, group:"dem_network_copartisan_vote", v:62}, {year:2013, group:"rep_network_copartisan_vote", v:59},
               {year:2016, group:"rep_no_close_dem_friends", v:14}, {year:2016, group:"dem_no_close_rep_friends", v:24},
               {year:2016, group:"rep_a_lot_outparty_friends", v:7}, {year:2016, group:"dem_a_lot_outparty_friends", v:6} ],
      sources:[ {label:"PRRI 2013 American Values Survey", url:"https://prri.org/research/poll-race-religion-politics-americans-social-networks/"},
                {label:"Pew 2016", url:"https://www.pewresearch.org/politics/2016/06/22/3-partisan-environments-views-of-political-conversations-and-disagreements/"} ]
    },
    {
      id:"residential_segregation", flag:"snapshot", unit:"%",
      label:"Partisan residential segregation (2018)",
      series:[ {year:2018, metric:"share_in_partisan_segregated_areas", v:98.5, note:"98-99% of voters; only Loving County TX mixes freely"} ],
      sources:[ {label:"Brown & Enos 2021 (Nature Human Behaviour)", url:"https://www.nature.com/articles/s41562-021-01066-z"} ]
    }
  ],

  /* ===== KICKER (enthusiast stat, not a bar) ===== */
  kicker: {
    id:"thanksgiving", flag:"solid",
    text:"In 2016, Thanksgiving dinners between cross-party precincts ran 30-50 minutes shorter (up to 50-70 min for travelers from Republican to Democratic areas). The effect TRIPLED in markets with heavy political advertising; there was no such effect in 2015.",
    source:{label:"Chen & Rohla 2018 (Science)", url:"https://www.science.org/doi/abs/10.1126/science.aaq1433"}
  },

  /* ===== RANDOM-MIXING BASELINE (derivation, not a citation) ===== */
  no_homophily_baseline: {
    note:"What cross-party ties would be with NO homophily, given party shares. Arithmetic, not a measured value.",
    all_edge_equal_thirds: {same_party:33, cross_party:67},
    partisan_only_equal_DR: {same_party:50, cross_party:50},
    realistic_shares: {p_D:0.30, p_R:0.28, p_I:0.42, same_party:34.5, cross_party:65.5},
    party_share_source:{label:"Pew party-affiliation fact sheet", url:"https://www.pewresearch.org/politics/fact-sheet/party-affiliation-fact-sheet-npors/"}
  },

  /* ===== HONEST GAPS (label these in the UI; do not fabricate) ===== */
  gaps: [
    "No cross-party FRIENDSHIP/network time series back to 1980 (Pew/PRRI start ~2013-2016; Mutz longitudinal anchor is 1996). Any 1980 friendship endpoint is an EXTRAPOLATION.",
    "Split-ticket / split-district count series not cleanly sourced (Abramowitz & Webster document the decline qualitatively).",
    "Partisan-dating time series not cleanly sourced.",
    "Mutz 2025 PNAS exact 1996-vs-2020 cross-cutting percentages are paywalled -- only the qualitative direction was obtained."
  ]
};
