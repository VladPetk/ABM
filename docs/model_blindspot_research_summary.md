# Consolidated Claude Deep Research: US Polarization Literature Sweep

This report aggregates the literature findings extracted from your interrupted Claude session. Multiple subagents performed research on US political polarization (1980–2025) to identify key empirical parameters, effect sizes, and constraints for your Agent-Based Model (ABM).

**Total Unique Sources Researched**: 30

---

## Relevance: HIGH

### Boxell, Gentzkow & Shapiro (2017) — Greater Internet use is not associated with faster growth in political polarization among US demographic groups, PNAS 114(40):10612–10617

- **URL**: <https://www.pnas.org/doi/10.1073/pnas.1706588114>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Pins the exact claim: across an index of nine polarization measures (1996–2016 ANES), polarization grew MORE among those 65+ than among 18–39 — i.e., fastest among the demographic groups LEAST likely to use the internet/social media — implying the internet explains only a small share of recent growth. This is the canonical anchor for 'who polarized' and a constraint on internet/media-driven ABM mechanisms: generational-replacement or online-exposure channels alone cannot reproduce the age gradient.

---

### Phillips (2022) — Affective Polarization: Over Time, Through the Generations, and During the Lifespan, Political Behavior 44:1483–1508

- **URL**: <https://link.springer.com/article/10.1007/s11109-022-09784-4>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The requested APC decomposition: affective polarization rises with PERIOD (out-party warmth falling faster than in-party warmth) and with AGE (via growing partisan strength, and for Republicans social sorting), with NO clear cohort effect on affective polarization itself — though Baby Boomer cohorts are chronically lower in both in- and out-party warmth, and each cohort enters the electorate more polarized than the last. Directly tells an ABM that polarization should be modeled as period+life-cycle, not cohort-driven.

---

### Correction for Boxell et al. (2018), PNAS — published correction to the 2017 demographic-groups paper

- **URL**: <https://www.pnas.org/doi/10.1073/pnas.1721401115>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Published correction to the 2017 PNAS paper — essential for the robustness/caveat column of the blind-spot register. Verifying what was corrected (data/coding details; the headline age-gradient finding stood) is exactly the kind of citation-precision check the register requires before pinning the Boxell et al. claim in docs/literature.md.

---

### Growing Up in a Polarized Party System: Ideological Divergence and Partisan Sorting Across Generations, Political Behavior (2024)

- **URL**: <https://link.springer.com/article/10.1007/s11109-024-09917-x>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- A 2024 cohort follow-up of the kind the question asks for (newer cohort decompositions 2022–2025): finds newer generations are on several issues LESS sorted than the generations they replace, tentatively implying generational replacement could gradually depolarize opinion — a direct check on the cohort_replacement rule's sign in the ABM and a partial counterweight to naive 'each cohort more polarized' assumptions.

---

### Voelkel et al. (2024), "Megastudy testing 25 treatments to reduce antidemocratic attitudes and partisan animosity," Science 386 (eadh4764), published Oct 17-18, 2024

- **URL**: <https://www.science.org/doi/10.1126/science.adh4764>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The single most-cited fact to verify: the Strengthening Democracy Challenge megastudy is Voelkel et al. 2024 in Science (not PNAS, not 2023). 25 crowdsourced interventions, ~32,000 participants. Partisan-animosity reductions were strongest for treatments highlighting sympathetic out-party individuals or common cross-partisan identities; antidemocratic-attitude reductions were strongest for correcting misperceptions of rival partisans' views and highlighting democratic-collapse threat. Key caveat for an ABM: animosity effects were 'surprisingly easy' but small-to-moderate, and a ~9,000-participant two-week follow-up found effects had waned significantly — durability is the binding constraint any intervention mechanism must reproduce.

---

### Mernyk, Pink, Druckman & Willer (2022), "Correcting inaccurate metaperceptions reduces Americans' support for partisan violence," PNAS 119(16) e2116851119

- **URL**: <https://www.pnas.org/doi/full/10.1073/pnas.2116851119>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Verifies the Mernyk et al. 2022 PNAS anchor: partisans greatly overestimate rival partisans' support for violence; correcting these metaperceptions reduces own support for and willingness to engage in partisan violence, with the largest effects among those with the largest misperceptions and effects enduring ~1 month — a notable durability exception versus the megastudy's two-week decay.

---

### Moore-Berg, Ankori-Karlinsky, Hameiri & Bruneau (2020), "Exaggerated meta-perceptions predict intergroup hostility between American political partisans," PNAS 117(26)

- **URL**: <https://www.pnas.org/doi/10.1073/pnas.2001263117>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Verifies the Moore-Berg et al. 2020 PNAS citation and effect size: partisans believe the out-party's prejudice/dehumanization toward them is roughly TWICE as strong as actually reported, and meta-prejudice/meta-dehumanization independently predict social distance and support for democratic-norm-flouting policies. Gives an ABM a concrete quantitative target: a ~2x exaggeration factor between actual and perceived out-party animus.

---

### Lees & Cikara, "Inaccurate group meta-perceptions drive negative out-group attributions in competitive contexts," Nature Human Behaviour 4 (published online 2019, issue March 2020)

- **URL**: <https://www.nature.com/articles/s41562-019-0766-4>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Verifies the Lees & Cikara anchor (note venue/year ambiguity: online Nov 2019, print 2020, Nature Human Behaviour). Seven experiments + one survey (n=4,282): people systematically overestimate out-group negativity in competitive (not cooperative) contexts; an informational correction reduced negative out-group attributions, most for the most inaccurate. Establishes the meta-perception bias as a general competitive-context mechanism, not US-politics-specific.

---

### "Correcting misperceptions of partisan opponents is not effective at treating democratic ills," PNAS Nexus 3(8) pgae304 (2024)

- **URL**: <https://academic.oup.com/pnasnexus/article/3/8/pgae304/7730165>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The major contested/replication caveat for mechanism class 1: a 2024 PNAS Nexus paper directly challenging the misperception-correction literature, finding corrections NOT effective at treating democratic ills. Essential for grading the correction→depolarization link 'mixed' rather than 'robust' in the blind-spot register — corrections reliably move metaperceptions, but downstream effects on animus/antidemocratic attitudes are disputed and short-lived.

---

### Boxell, Gentzkow & Shapiro (2024), "Cross-Country Trends in Affective Polarization," Review of Economics and Statistics 106(2): 557-565

- **URL**: <https://direct.mit.edu/rest/article/doi/10.1162/rest_a_01160/109262/Cross-Country-Trends-in-Affective-Polarization>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The key contrarian anchor for class 6: across 12 OECD countries the US shows the largest affective-polarization rise while 6 countries declined, a pattern the authors argue is inconsistent with universal drivers like rising economic inequality (and the internet) and more consistent with US-distinctive factors (party composition, racial divisions, partisan cable news). Directly downgrades the inequality-polarization link from causal to correlational/US-confounded for the ABM blind-spot register.

---

### Guess et al. (2023), "How do social media feed algorithms affect attitudes and behavior in an election campaign?" Science 381(6656)

- **URL**: <https://www.science.org/doi/10.1126/science.abp9364>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Flagship paper of the Meta US 2020 Facebook & Instagram Election Study (3 papers in Science + 1 in Nature): replacing algorithmic ranking with reverse-chronological feeds for ~3 months changed on-platform exposure substantially but produced no measurable effects on affective polarization, ideological extremity, or issue positions. The single most important 2023-2025 field-experimental result the ABM's partisan-media mechanism should be benchmarked against (algorithmic curation as a weak short-run polarization lever).

---

### Science news (2023): critics dispute the Meta 2020 null-polarization finding (63 'break-glass' algorithm changes contaminated the control condition)

- **URL**: <https://www.science.org/content/article/study-found-facebook-algorithm-didnt-promote-political-polarization-critics-doubt>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The essential robustness caveat for grading the Meta studies 'mixed' rather than 'robust': Meta deployed ~63 emergency news-feed changes during the study window, altering the control condition, so the null effect on polarization may not generalize to the normal algorithm. Needed for an honest evidence-grade entry in the blind-spot register.

---

### McCarty, Poole & Rosenthal, "Political Polarization and Income Inequality" (SSRN working paper underlying Polarized America, 2006 MIT Press)

- **URL**: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1154098>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The canonical class-6 citation: century-long time-series showing congressional polarization (DW-NOMINATE) and income inequality (Gini, top shares) move together, falling mid-century and rising post-1970s. The authors themselves concede the causal case is circumstantial ('no smoking gun') — the correlation is robust, the causal arrow is not established, which is exactly the grading the register needs.

---

### Hall (2015), "What Happens When Extremists Win Primaries?", APSR 109(1): 18-42

- **URL**: <https://www.andrewbenjaminhall.com/Hall_APSR.pdf>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Primary-source PDF of the key candidate-selection anchor: RD design on coin-flip US House primaries 1980-2010 shows nominating an extremist cuts the party's general-election vote share ~9-13 pp and win probability 35-54 pp — yet extremists keep getting nominated, grounding an endogenous mass→elite selection mechanism with measured effect sizes. Robust (widely cited RD design); pairs with Hall's later book 'Who Wants to Run?' (2019) on candidate self-selection.

---

### Bafumi & Herron (2010), "Leapfrog Representation and Extremism", APSR 104(3): 519-542

- **URL**: <https://www.cambridge.org/core/journals/american-political-science-review/article/abs/leapfrog-representation-and-extremism-a-study-of-american-voters-and-their-members-in-congress/7F30201FBE6E3092D705FC06C6777DB9>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Verified primary citation for leapfrog representation: joint-scaling of voters and MCs shows members are more extreme than their constituents, and when a seat flips parties it 'leapfrogs' the median voter — an extremist of one side replaced by an extremist of the other. Robust descriptive finding; directly specifies what an ABM elite-replacement rule must reproduce (over-extremity + party-flip overshoot, not median convergence).

---

### Barber (2016), "Ideological Donors, Contribution Limits, and the Polarization of American Legislatures", Journal of Politics 78(1): 296-310

- **URL**: <https://www.journals.uchicago.edu/doi/abs/10.1086/683453>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The donor-influence anchor, verified at venue: original 20-year state contribution-limit dataset shows higher individual-contribution limits select more polarized legislators while higher PAC limits select more moderate ones — ideological individual donors vs access-seeking PACs. Mixed-to-robust (quasi-experimental state variation, not RCT); grounds a feedback channel where activist mass donors pull elite positions outward.

---

### Thomsen (2017), "Opting Out of Congress: Partisan Polarization and the Decline of Moderate Candidates", Cambridge UP

- **URL**: <https://www.cambridge.org/core/books/opting-out-of-congress/8DE674781E5A3FBFE93287A9EA84F7D0>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Verified citation for the 'party fit' self-selection mechanism: moderates increasingly decline to run for Congress at all, so elite polarization grows via the candidate pool, not just voter choice — complementary to Hall and distinct from primary-electorate explanations. Robust; an ABM mass→elite module anchored here needs an entry/exit decision dependent on distance from the party's current elite centroid.

---

### Leonard, Lipsitz, Bizyaeva, Franci & Lelkes (2021), "The nonlinear feedback dynamics of asymmetric political polarization", PNAS 118(50)

- **URL**: <https://www.pnas.org/doi/10.1073/pnas.2102149118>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Directly on both bundled classes: a formal feedback model fit to DW-NOMINATE showing post-1980s party-mean dynamics (especially the steeper Republican shift) are best explained by self-reinforcing intraparty feedback rather than exogenous drift — the closest published template for replacing an ABM's exogenous elite schedule with a feedback-coupled one, and it quantifies the asymmetry. Note DW-NOMINATE asymmetry itself carries methodological caveats (roll-call agenda control; scores ill-suited to cross-era cardinal comparison).

---

### Egan (2020), AJPS 64(3): 699-716 — "Identity as Dependent Variable: How Americans Shift Their Identities to Align with Their Politics"

- **URL**: <https://onlinelibrary.wiley.com/doi/10.1111/ajps.12496>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Core anchor for class 4 (identity as DV). Panel data over 4 years shows small-but-significant shares of Americans switch ethnic, religious, sexual-orientation, and class identities in directions predicted by their prior partisanship/ideology — reversing the 'unmoved mover' assumption. Magnitude note for the ABM: the effect is real but small (a thin tail of switchers, not mass identity churn), so an ABM mechanism anchored here should produce modest reverse-flow identity alignment, not wholesale resorting. Robust (single-author but widely cited, panel-based).

---

### Margolis (2018), University of Chicago Press — "From Politics to the Pews: How Partisanship and the Political Environment Shape Religious Identity"

- **URL**: <https://press.uchicago.edu/ucp/books/book/chicago/F/bo28246146.html>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The book-length anchor for partisanship→religion reverse causation: panel data plus original randomized experiments show religious identification and involvement respond to partisan identity (acquired in early adulthood before religious re-engagement), explaining part of the 'God gap.' Robust — well-reviewed in POQ and Sociology of Religion; complements Egan by establishing mechanism and timing (life-cycle window) an ABM would need: identity drift gated on party, strongest among weakly anchored/young agents.

---

### Prior (2013), Annual Review of Political Science 16: 101-127 — "Media and Political Polarization"

- **URL**: <https://www.annualreviews.org/content/journals/10.1146/annurev-polisci-100711-135242>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The essential skeptical strand for class 5 grading: ideologically one-sided news exposure is confined to a small, highly involved segment; 'no firm evidence that partisan media are making ordinary Americans more partisan.' Implies an ABM's media-diet distribution must be heavy-tailed (most agents moderate/low-dose, a small extreme tail), and direct media persuasion effects should be small for typical agents. Robust as a review; marks the partisan-media-as-mass-driver claim as contested.

---

### Guess (2021), AJPS 65(4): 1007-1022 — "(Almost) Everything in Moderation: New Evidence on Americans' Online Media Diets"

- **URL**: <https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12589>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- Behavioral (web-tracking) confirmation of Prior's skepticism: ~65% overlap (2015) / ~50% (2016) between Democrats' and Republicans' media diets, mostly moderate/mainstream; echo chambers real only for a small partisan minority driving disproportionate traffic to slanted sites. Robust (passive browsing data, two waves). Direct calibration target for the ABM's media_diet selective-exposure magnitude — the model must NOT produce population-wide echo chambers.

---

### Gentzkow & Shapiro (2010), Econometrica 78(1): 35-71 — "What Drives Media Slant? Evidence from U.S. Daily Newspapers"

- **URL**: <https://www.econometricsociety.org/publications/econometrica/2010/01/01/what-drives-media-slant-evidence-us-daily-newspapers>
- **Relevance Grade**: `high`

#### Findings & Key Takeaways:
- The supply-side arrow-reversal anchor: text-based slant index plus a structural demand model shows reader preferences for like-minded news explain ~20% of slant variation, while owner identity explains far less — outlets chase audiences, demand drives slant. Robust (canonical, structural). Grounds an outlet-positioning feedback rule (outlets drift toward their audience's centroid) rather than treating outlet slant as exogenous — directly relevant to polarlab's pending Phase B feedback work.

---

## Relevance: MEDIUM

### Generational Change in Affective Polarization and Partisanship: An Age-Period-Cohort Accounting (APSA Preprints)

- **URL**: <https://preprints.apsanet.org/engage/apsa/article-details/5f73663eac50fe0018d65ec4>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- A second APC accounting on ANES 1964–2016 covering generational replacement's role in affective polarization, independent identification, and the decline of the Democratic plurality; corroborates Phillips's Boomer-cohort warmth dip (lower in- AND out-party warmth, hence no net cohort effect on polarization). Caveat for citation precision: this is a preprint — verify whether/where it was eventually published before citing in literature.md.

---

### Boxell, Gentzkow & Shapiro (2024) — Cross-Country Trends in Affective Polarization, Review of Economics and Statistics 106(2):557–565

- **URL**: <https://direct.mit.edu/rest/article/106/2/557/109262/Cross-Country-Trends-in-Affective-Polarization>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- The same authors' published follow-up: US shows the largest affective-polarization increase among 12 OECD countries; digital-media penetration is weakly/negatively associated with polarization trends while 24-hour partisan news, partisan sorting, and elite polarization are positively associated. Useful supporting context for the register's period-effect/driver framing (consistent with the 2017 internet-skepticism result), though it is cross-national rather than an APC decomposition.

---

### Stanford Sociology summary: "Scalable interventions reduce polarization, support for partisan violence, and anti-democratic attitudes" (Strengthening Democracy Challenge)

- **URL**: <https://sociology.stanford.edu/scalable-interventions-reduce-polarization-support-partisan-violence-and-anti-democratic-attitudes>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- Project-side summary of the megastudy useful for cross-checking design details: 252 crowdsourced ideas narrowed to 25 tested interventions; confirms the dissociation that partisan animosity was easier to reduce than support for partisan violence or undemocratic practices — a two-axis outcome structure that maps directly onto the model's separate issue-sorting vs affect measurement axes.

---

### "Income Inequality and Congressional Republican Position Taking, 1913–2013," Journal of Politics 81(4), 2019

- **URL**: <https://www.journals.uchicago.edu/doi/10.1086/704787>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- Serious published pushback on the McCarty-Poole-Rosenthal coupling: inequality tracks Republican position-taking specifically (not symmetric two-party polarization), and Democratic leftward movement corresponds to decreasing inequality — reframing the inequality-polarization correlation as an asymmetric-polarization artifact. Useful for both class 6 and the class 7 asymmetry discussion.

---

### Allcott et al. (2024), "The effects of Facebook and Instagram on the 2020 election: A deactivation experiment," PNAS 121

- **URL**: <https://www.pnas.org/doi/10.1073/pnas.2321584121>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- Companion class-8 evidence: paying ~35k users to deactivate Facebook/Instagram for 6 weeks before the 2020 election produced small/no detectable effects on affective polarization and candidate evaluations (some knowledge and well-being effects). Together with Guess et al., it bounds the short-run causal contribution of social-media exposure — a constraint an ABM media-rule magnitude should respect.

---

### Hacker & Pierson, "Confronting Asymmetric Polarization", in Persily ed., Solutions to Political Polarization in America (Cambridge, 2015)

- **URL**: <https://www.cambridge.org/core/books/abs/solutions-to-political-polarization-in-america/confronting-asymmetric-polarization/3966003B2517E22BF288796AC4985F34>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- Verified venue for the Hacker & Pierson asymmetric-polarization statement (DW-NOMINATE shows the Republican median moved ~0.25+ while Democrats stayed near -0.3/-0.4); the same volume contains the counter-position chapters, making it a one-stop source for the claim plus its serious pushback. Asymmetry in elite roll-call space is robust per NOMINATE's own creators ('a Republican-led phenomenon'), but contested as an ideology measure (Democratic movement may hide in agenda control and group-interest politics per Grossmann & Hopkins, Asymmetric Politics, OUP 2016).

---

### Martin & Yurukoglu (2017), American Economic Review 107(9): 2565-2599 — "Bias in Cable News: Persuasion and Polarization"

- **URL**: <https://www.aeaweb.org/articles?id=10.1257%2Faer.20160812>
- **Relevance Grade**: `medium`

#### Findings & Key Takeaways:
- Closes the loop between classes 5's two halves: structural model where viewers select into slanted cable news AND their ideologies evolve from exposure (channel-position IV; Fox adds ~0.3pp Republican vote share per 2.5 extra min/week; no symmetric CNN/MSNBC effect). Robust identification but effect sizes debated relative to survey-based null results. For the ABM: the taste-for-like-minded-news + persuasion feedback loop is exactly the endogenous media-selection coupling, and it quantifies how small per-dose persuasion must be.

---

