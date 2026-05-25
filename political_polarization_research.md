# Political Polarization: A Literature Review and Modeler's Synthesis for Agent-Based Modeling

## TL;DR
- **Polarization is best understood as a multi-component phenomenon driven primarily by social-identity sorting**, not by ideological disagreement alone: a "mega-identity" stack (party + race + religion + geography + culture) generates affective animosity that outpaces issue-based polarization (Iyengar et al. 2019; Mason 2018; Finkel et al. 2020). For ABM purposes, agents need *both* an identity vector and an issue vector, with sorting (alignment) as a key state variable.
- **The dominant ABM toolkit** consists of bounded-confidence (Deffuant; Hegselmann–Krause), Axelrod-style homophily+assimilation, negative-influence/repulsion (Macy–Flache, Baldassarri–Bearman), argument-communication (Mäs–Flache 2013), reinforcement-learning (Banisch–Olbrich 2019), and culture-network co-evolution (DellaPosta–Shi–Macy 2015). Each predicts polarization under different parameter regimes (confidence threshold ε, homophily h, network modularity Q, F/q feature-trait ratio), and the field's open question is which micro-rule best matches empirical opinion data.
- **Institutional and structural moderators matter**: majoritarian / two-party electoral systems show higher affective polarization than proportional systems; elite ideological divergence amplifies mass sorting; partisan media and high-modularity networks reinforce polarization; cross-national evidence (Boxell, Gentzkow & Shapiro 2022; Gidron, Adams & Horne 2020) shows the US is the fastest-polarizing among advanced democracies but not the most polarized. A defensible ABM must parameterize the institutional context, not just micro-interaction rules.

## Key Findings

1. **Affective polarization (out-party dislike) has risen sharply in the US, while ideological polarization in the mass public has risen only modestly.** Iyengar, Sood & Lelkes (2012, *Public Opinion Quarterly*) introduced the concept; Iyengar, Lelkes, Levendusky, Malhotra & Westwood (2019, *Annual Review of Political Science* 22:129–146) report that the percentage of partisans reporting "very unfavorable" views of the other party more than doubled (from ~20% in 1994 to ~55% in 2016, per Pew data cited therein) and the out-party feeling-thermometer gap widened from ~20° in the 1970s to ~40° by 2012. Finkel et al. (*Science* 2020, 370:533–536) report that out-party feeling-thermometer scores fell from ~48° in the 1970s to ~20° today, while in-party affect remained around 70–75°. Out-party animus now predicts vote choice more strongly than in-party warmth.

2. **Partisanship is best modeled as a social identity, not a Bayesian running tally.** Green, Palmquist & Schickler (2002, *Partisan Hearts and Minds*); Huddy, Mason & Aarøe (2015, *APSR* 109:1–17) on "expressive partisanship"; Greene (2004) on the IDPG identification scale — all converge on Tajfel/Turner social-identity theory as the micro-foundation. Mason (2015, 2018) shows that alignment ("sorting") of partisan identity with race, religion, ideology, and geography is what drives affective polarization, even controlling for issue distance.

3. **Elite polarization precedes and amplifies mass sorting.** Hetherington (2001, *APSR* 95:619–631) shows that elite ideological clarity since the 1970s caused resurgent mass partisanship; McCarty, Poole & Rosenthal (2006, *Polarized America*) document the steady divergence of Congressional voting via DW-NOMINATE; Levendusky (2009, *The Partisan Sort*) shows mass partisan-ideological sorting follows elite cues.

4. **Cross-national evidence shows polarization is not a US-only or universal trend.** Boxell, Gentzkow & Shapiro (NBER WP 26669; *Review of Economics and Statistics* 2022) analyze nine OECD democracies 1975–2017: affective polarization rose fastest in the US, but fell in some countries (e.g., Germany, Sweden) and was stable elsewhere. Reiljan (2020, *European Journal of Political Research*) and Wagner (2021, *Electoral Studies*) construct the Affective Polarization Index used in Comparative Study of Electoral Systems data; Gidron, Adams & Horne (2020, *American Affective Polarization in Comparative Perspective*) confirm heterogeneous trends across 20 democracies. The US is an outlier in *rate of change*, not in *level*.

5. **Echo-chamber and filter-bubble effects are smaller and more contested than the popular narrative suggests, but partisan-media effects on heavy consumers are real.** The Reuters Institute review (Ross Arguedas, Robertson, Fletcher & Nielsen, January 2022, *Echo Chambers, Filter Bubbles, and Polarisation: A Literature Review*) concludes that "scholarship suggests echo chambers are much less widespread than is commonly assumed, finds no support for the filter bubble hypothesis." Bail et al. (*PNAS* 2018, 115:9216–9221) found that *exposure* to opposing Twitter content *increased* polarization among Republicans (a backfire effect). Levendusky (2013, *AJPS* 57:611–623; *How Partisan Media Polarize America*, 2013) shows partisan cable polarizes those who already watch it. Guess et al. (*Science* 381:398–404, 2023) report from the Meta/US 2020 Election Study that switching Facebook users to a chronological feed "did not significantly alter levels of issue polarization, affective polarization, political knowledge, or other key attitudes during the 3-month study period"; Nyhan et al. (*Nature*, 2023) confirm the same null finding across ~23,000 Facebook/Instagram users.

6. **Residential and social-network sorting are real but partial.** Bishop's "Big Sort" thesis (2008) is partly supported by Brown & Enos (2021, *Nature Human Behaviour*) showing rising partisan neighborhood segregation, but Abrams & Fiorina (2012, *PS: Political Science & Politics*) and Martin & Webster (2020, *Political Science Research and Methods*) show residential sorting is largely *inadvertent* (correlated lifestyle preferences) rather than driven by partisan intent. McPherson, Smith-Lovin & Cook (2001, *Annual Review of Sociology* 27:415–444) on homophily provides the canonical theoretical mechanism.

7. **Motivated reasoning is robust at the individual level.** Taber & Lodge (2006, *AJPS* 50:755–769) — the canonical "Motivated Skepticism" paper — show subjects exhibit prior-attitude effects, disconfirmation bias, and confirmation bias when evaluating political arguments; effects are *larger* for the more politically sophisticated. Lodge & Taber (2013, *The Rationalizing Voter*) generalize this to "hot cognition." Lord, Ross & Lepper (1979) established the foundational "biased assimilation" finding.

8. **Institutional context shapes polarization.** Comparative work (Gidron, Adams & Horne 2020; McCoy & Somer 2019 on "pernicious polarization") finds that majoritarian electoral systems and presidentialism are associated with higher affective polarization than proportional / coalition systems. McCoy, Rahman & Somer (2018, *American Behavioral Scientist* 62:16–42) and McCoy & Somer (2019, *Annals of AAPSS*) argue pernicious polarization emerges when political entrepreneurs deliberately exploit existing cleavages with "Us vs. Them" discourse.

## Details

### 1. Core drivers of political polarization

**Affective polarization** (Iyengar, Sood & Lelkes 2012) is the tendency for partisans to evaluate co-partisans positively and out-partisans negatively. It is operationalized via feeling-thermometer differences (in-party minus out-party), social-distance items (would you object to a child marrying across party lines?), and discriminatory behavior in economic games (Iyengar & Westwood 2015, *AJPS*). The Iyengar et al. (2019) *Annual Review* synthesis is the field's standard reference: out-party animus has more than doubled since the 1990s and is largely driven by *increasing distaste for the out-party* rather than rising warmth for one's own.

**Ideological polarization** in the mass public is contested. Fiorina & Abrams (2008, *Annual Review of Political Science*) argue that mass attitudes have not significantly diverged; Abramowitz (2010, *The Disappearing Center*) argues the engaged public *has* polarized. The consensus position: mean issue positions have moved modestly, but issue positions have become *better sorted* by party (Levendusky 2009) and *constrained* in ideological bundles (Baldassarri & Gelman 2008, *AJS*).

**Social sorting** (Mason 2015, *Public Opinion Quarterly* 80:351–377, "A Cross-Cutting Calm"; Mason 2018, *Uncivil Agreement*) is the mechanism linking ideological and affective polarization: as racial, religious, and ideological identities have come to align with partisanship, partisans now perceive maximum group difference. Mason shows that *sorted* partisans display higher affective polarization even controlling for their actual issue positions.

**Media effects** operate at two scales. At the elite/broadcast scale, Prior (2007, *Post-Broadcast Democracy*) and Martin & Yurukoglu (2017, *American Economic Review*) show partisan cable (notably Fox News) shifts vote choice; Levendusky (2013, AJPS) shows partisan-media exposure polarizes its (self-selected) viewers via motivated reasoning. At the social-media scale, evidence is mixed: filter-bubble claims (Pariser 2011; Sunstein 2018) receive weak empirical support per Barberá (2020), Guess (2021), and the Reuters Institute review (Ross Arguedas et al. 2022).

**Elite polarization** (McCarty, Poole & Rosenthal 2006) is measured via DW-NOMINATE scores of congressional voting and shows nearly monotonic divergence since the 1970s, primarily driven by Republican rightward movement. Hetherington (2001) demonstrates that elite polarization *clarifies* party brands for voters, raising mass partisanship.

### 2. Party identification and partisan sorting

The classical "Michigan model" (Campbell et al. 1960, *The American Voter*) treats party ID as an early-life socialized affective attachment. The modern social-identity reformulation (Greene 1999, 2004; Huddy 2001; Huddy, Mason & Aarøe 2015 APSR) draws on Tajfel & Turner's (1979, 1986) social-identity theory: partisans derive self-esteem from in-group belonging, exhibit in-group favoritism, and respond to identity threat with hostility toward the out-group.

Mason's (2018) "mega-identity" thesis is the key recent integration: when partisan identity overlaps with racial, religious, ideological, and lifestyle identities, the psychological stakes of each election rise. Sorting predicts: (a) emotional reactivity, (b) partisan prejudice, and (c) increased activism, *independently of issue positions*. Iyengar & Krupenkin (2018, *Advances in Political Psychology*) document the "strengthening of partisan affect" since 2000.

**ABM-relevant variables:** identity strength (continuous), number of overlapping identities, identity-issue correlation matrix (sorting parameter), perceived threat (modulated by environment).

### 3. Belief updating and opinion dynamics

The dominant micro-theory in political psychology is **motivated reasoning** (Kunda 1990, *Psychological Bulletin*; Taber & Lodge 2006). Subjects engage in: (i) *prior-attitude effect* — congruent arguments rated stronger; (ii) *disconfirmation bias* — counter-attitudinal information is counter-argued more; (iii) *confirmation bias* — selective search; (iv) *attitude polarization* — exposure to balanced information *strengthens* prior attitudes. Crucially, political sophistication *worsens* bias rather than mitigating it. Lord, Ross & Lepper (1979) established the foundational "biased assimilation" finding.

**Social-influence theories** for ABMs: Friedkin–Johnsen (1990, 1999) weighted averaging with anchoring on initial position; DeGroot (1974) consensus formation; Deffuant et al. (2000, *Advances in Complex Systems*) and Hegselmann & Krause (2002, *JASSS* 5(3)) bounded-confidence — agents only update when opinion distance < ε; Axelrod (1997) homophily-driven trait copying.

**Echo chambers and network homophily.** McPherson, Smith-Lovin & Cook (2001) is the canonical homophily review. Political-discussion networks are strongly homophilous (Huckfeldt & Sprague 1995; Mutz 2006, *Hearing the Other Side*). On social media, Cinelli et al. (2021, *PNAS*) document echo chambers on Facebook/Twitter; Barberá et al. (2015, *Psychological Science*) document them more strongly for political than for non-political topics.

### 4. Systemic and institutional factors

**Electoral systems.** A small but growing comparative literature finds:
- Affective polarization is on average *higher* in majoritarian than in proportional systems (Gidron, Adams & Horne 2020). A 19-country study cited in the New America Foundation synthesis finds winner-take-all systems are "associated with partisans' more negative feelings toward opposing parties," while "proportional systems are associated with positive partisan affect."
- Pernicious polarization (McCoy & Somer 2019, *Annals of AAPSS*; their 11-country study) emerges most acutely under majoritarian/presidential institutions with strong "Us vs. Them" entrepreneurs.

**Two-party vs. multiparty.** Two-party systems mechanically reduce the cognitive complexity of partisanship to a binary in/out distinction, intensifying SIT-style intergroup dynamics. Multiparty systems allow cross-cutting affect (citizens can like more than one out-party), as Wagner (2021) shows with his weighted-distance measure.

**Gerrymandering and primary elections.** McGhee et al. (2014, *AJPS*) and Hill & Tausanovitch (2018, *Journal of Politics*) provide mixed evidence: gerrymandering's direct effect on legislator extremism is small to modest; primary electorates (Hill 2015) are not systematically more extreme than general electorates, undercutting the simple "primaries cause extremism" story.

**Media environments.** Prior (2007) shows that the shift from broadcast to fragmented cable + internet markets enabled "selective exposure"; before cable, low-interest viewers were *incidentally* exposed to news, dampening polarization. Martin & Yurukoglu (2017) estimate Fox News causally shifted Republican vote share by 0.5 percentage points in 2000 and 6.0 in 2008.

### 5. Social and structural factors

**Geography and residential sorting.** Bishop (2008, *The Big Sort*) argued counties were increasingly "landslide" counties; Abrams & Fiorina (2012, *PS*) sharply critiqued the inference, noting county-level data overstate true neighborhood sorting. Brown & Enos (2021, *Nature Human Behaviour*) using precinct-level voter file data find substantial and growing partisan exposure asymmetry. Martin & Webster (2020, *PSRM*) decompose sorting into "inadvertent" (lifestyle preferences correlated with partisanship) and "intentional" (direct partisan preference); they find inadvertent sorting dominates.

**Network homophily.** Mutz (2006) shows Americans' political-discussion networks are strikingly partisan-homogeneous and that exposure to disagreement reduces participation (the "cross-cutting calm" effect, also in Mason 2016).

**Socioeconomic inequality.** McCarty, Poole & Rosenthal (2006) link rising elite polarization to rising income inequality; Bonica et al. (2013, *Journal of Economic Perspectives*) document how donor extremism amplifies elite divergence; Bartels (2008, *Unequal Democracy*) ties income inequality to representational distortion.

**Cultural change and generational shifts.** Inglehart's value-change thesis (post-materialism), the rise of identity politics post-1965 civil-rights realignment (Carmines & Stimson 1989, *Issue Evolution*; Mason 2018), and generational replacement all contribute. Phillips (2022, *Political Behavior* 44:1483–1508) "Affective Polarization: Over Time, Through the Generations, and During the Lifespan" decomposes the rise into period, cohort, and life-cycle components.

### 6. Key empirical findings (the stylized facts an ABM should reproduce)

1. Affective polarization has risen ~30 percentage points faster than ideological polarization in the US since 1980 (Iyengar et al. 2019).
2. Partisan-identity strength predicts emotional and behavioral reactions to political events more strongly than issue positions (Huddy, Mason & Aarøe 2015).
3. Out-party feeling thermometers in the US dropped from ~48° (1978) to ~20° (2020); in-party stable at ~70° (Finkel et al. 2020).
4. Cross-nationally, polarization trends are heterogeneous; the US is an outlier in *change*, not in *level* (Boxell, Gentzkow & Shapiro 2022; Gidron et al. 2020).
5. Sorted partisans (high identity alignment) show higher affective polarization at given ideological distance (Mason 2015, 2018).
6. Exposure to opposing partisan content can *increase* polarization (Bail et al. 2018 PNAS); cross-cutting exposure under the right conditions reduces it (Levendusky 2021, *Our Common Bonds*).
7. Elite polarization (DW-NOMINATE) has risen monotonically since the 1970s, asymmetrically driven by Republican movement (McCarty, Poole & Rosenthal 2006).
8. Residential and network homophily are real but only partly explain geographic political clustering (Brown & Enos 2021; Martin & Webster 2020).
9. Partisan-media effects are concentrated among the small set of heavy consumers but spill over via interpersonal discussion (Druckman, Levendusky & McLain 2018, AJPS).
10. Echo chambers are present on social media but most users still encounter cross-cutting content; algorithmic filter bubbles produce small effects on diversity (Barberá 2020; Reuters Institute review 2022; Bakshy, Messing & Adamic 2015, *Science*; Guess et al. 2023, *Science*).

### 7. Agent-based modeling of polarization

The ABM literature on polarization spans four families.

**Family A — Bounded-confidence and consensus models.**
- **Deffuant, Neau, Amblard & Weisbuch (2000)**, *Advances in Complex Systems* 3:87–98. Agents have continuous opinions ∈ [0,1]; a random pair is selected; if |x_i − x_j| < threshold d, both move toward each other by μ·(x_j − x_i). Key parameters: confidence threshold d (lower → more clusters), convergence rate μ. Produces consensus, polarization (2 clusters), or fragmentation depending on d.
- **Hegselmann & Krause (2002)**, *JASSS* 5(3):2. Each agent at each time step averages over *all* neighbors within ε. Synchronous; produces fewer, larger clusters than Deffuant for the same ε. Key parameter: ε (confidence radius). Heterogeneous ε (Kou et al. 2012) produces richer dynamics.
- *Limitation:* Both models *only* generate polarization from initial disagreement and bounded confidence; they cannot generate extremization beyond the initial range without modification (Deffuant 2002 added extremists).

**Family B — Homophily + assimilation with multi-trait culture.**
- **Axelrod (1997)**, *Journal of Conflict Resolution* 41(2):203–226. Agents on L×L lattice (von Neumann neighborhood) have a vector of F features each with q possible traits. Interaction probability = cultural similarity (n_kr/F); on interaction, copy one differing trait. Produces "local convergence with global polarization." Theoretical analysis (Castellano, Marsili & Vespignani 2000; Klemm et al. 2003; Vilone et al.) shows F > q tends to monoculture, F < q to fragmentation; counter-intuitively, increasing territory size can *decrease* the number of coexisting cultures beyond a threshold.
- **DellaPosta, Shi & Macy (2015)**, *American Journal of Sociology* 120(5):1473–1511. Extends Axelrod's homophily+assimilation to ideology + lifestyle traits. The authors write: "Computational experiments show how the self-reinforcing dynamics of homophily and influence dramatically amplify even very small elective affinities between lifestyle and ideology, producing a stereotypical world of 'latte liberals' and 'bird-hunting conservatives' much like the one in which we live." Validated against 22,572 pairwise GSS correlations (1972–2010).

**Family C — Negative influence / repulsion / argument-based models.**
- **Macy, Kitts, Flache & Benard (2003)** in *Dynamic Social Network Modeling and Analysis* (National Academies Press). A Hopfield-attractor extension to social influence; tie weights w_ij can be positive (homophily/attraction) or negative (xenophobia/repulsion). Bipolar (two-faction) polarization is the unique global attractor; pluralistic equilibria emerge only when N is large relative to issue space. Quote: "Agents are attracted to others with similar states (the principle of homophily) and are also influenced by others, as conditioned by the strength and valence of the social tie. Negative valence implies xenophobia (instead of homophily) and differentiation (instead of imitation)... networks can self-organize into two antagonistic factions, without the knowledge or intent of the agents."
- **Baldassarri & Bearman (2007)**, *American Sociological Review* 72(5):784–811, "Dynamics of Political Polarization." Multi-issue agents with bivalent influence and issue salience. Reproduces two paradoxes: "global attitude polarization is relatively rare, even though pundits describe it as common"; and "while individuals experience attitude homogeneity in their interpersonal networks, their networks are characterized by attitude heterogeneity." Take-off issues with high salience drive episodic polarization while selective discussion makes local environments feel homogeneous.
- **Flache & Macy (2011)**, *Journal of Mathematical Sociology* 35:146–176, "Small Worlds and Cultural Polarization." Bivalent-influence Axelrod model on small-world networks. Long-range "bridge" ties promote consensus under positive influence but *reverse* under bivalent (xenophobic) influence: "even very small amounts of contact [between clusters can produce polarization]... This result should caution modelers of cultural dynamics against overestimating the integrative effects of greater cultural contact."
- **Mäs & Flache (2013)**, *PLOS ONE* 8(11):e74516, "Differentiation without Distancing" — the Argument Communication Theory of Bi-Polarization (ACTB). Each agent has an attitude AND an underlying pool of pro/con arguments; homophily at the attitude level + argument exchange produces bi-polarization *without* negative influence; bi-polarization emerges when the homophily parameter h ≥ ~3. Empirically validated with N=96 group-discussion experiment. Quote: "Due to homophily, actors interact mainly with others whose arguments will intensify existing tendencies for or against the issue at stake... Results demonstrate that argument exchange can entail bi-polarization even when there is no negative influence."
- **Banisch & Olbrich (2019)**, *Journal of Mathematical Sociology* 43(2):76–103, "Opinion polarization by learning from social feedback." Reinforcement-learning ABM: agents have Q-values for opinion options; expressing an opinion to a neighbor returns binary agreement/disagreement reward. In networks of sufficient modularity, distinct groups converge to opposed opinions. Quote: "While previous models have emphasized the polarization effects of deliberative argument-based communication, our model highlights an affective experience-based route to polarization."
- **Duggins (2017)**, arXiv:1406.7770 — "A Psychologically-Motivated Model of Opinion Change." Includes intolerance, susceptibility, conformity, and extremists; reproduces sustained "strong diversity," subcultures, and pluralistic ignorance, calibrated to two US political-opinion datasets.
- **Leifeld (2014)**, *Computational Social Networks* 1:7, "Polarization of coalitions in an agent-based model of political discourse."

**Family D — Co-evolutionary and network-rewiring models.**
- **Centola, González-Avella, Eguíluz & San Miguel (2007)**, *AJS*: co-evolution of cultural similarity and network ties — agents drop ties to fully-dissimilar neighbors and form new ones. Polarization is more robust to noise.
- **Schelling (1971)**, *Journal of Mathematical Sociology*: while developed for racial residential segregation, Schelling's residential-sorting model is widely cited as the canonical ABM showing that mild individual homophily preferences (preferring at least ~30% same-type neighbors) produce extreme segregation. Directly relevant to residential partisan sorting.

**Family E — Synthesis paper for conceptual framing (not an ABM).**
- **Finkel et al. (2020)**, *Science* 370:533–536, "Political Sectarianism in America" defines the construct as the conjunction of three components: (i) **othering** — "the tendency to view opposing partisans as essentially different or alien to oneself"; (ii) **aversion** — "the tendency to dislike and distrust opposing partisans"; (iii) **moralization** — "the tendency to view opposing partisans as iniquitous." This framework is increasingly used as the *target* construct ABMs should reproduce.

**Major reviews/synthesis:**
- Castellano, Fortunato & Loreto (2009), *Reviews of Modern Physics* 81:591–646 — "Statistical physics of social dynamics" — comprehensive review of opinion-dynamics models.
- **Flache, Mäs, Feliciani, Chattoe-Brown, Deffuant, Huet & Lorenz (2017)**, *JASSS* 20(4):2 — "Models of Social Influence: Towards the Next Frontiers" — the standard ABM-opinion-dynamics review. Identifies three ideal-typical outcomes: consensus, bi-polarization, fragmentation. Distinguishes *assimilative*, *similarity-biased* (bounded confidence / homophily), and *repulsive* (negative-influence) families.

### Modeler's synthesis: candidate ABM rules and parameters

Below is a proposed minimum specification for an ABM of US political polarization integrating the literature.

**Agent state vector** (per agent i):
- Partisan identity P_i ∈ {D, R, Independent} with strength s_i ∈ [0,1].
- Identity vector I_i ∈ ℝ^k for k cross-cutting identities (race, religion, geography, class) — used to compute alignment.
- Issue vector X_i ∈ [−1,1]^m for m issues with per-issue salience w_im.
- Argument pool A_i (vector of pro/con arguments per issue, à la Mäs–Flache).
- Affect vector (in-party warmth minus out-party warmth per opposed group).
- Media diet / exposure parameter.

**Macro / contextual parameters:**
- Electoral system (binary majoritarian vs. PR multiplier on intergroup affect).
- Elite ideological distance Δ_elite (exogenous time series or co-evolving).
- Media-environment fragmentation φ.
- Network topology (small-world with rewiring β; community modularity Q).

**Interaction rules** (per time step):
1. *Encounter:* Pair sampled from network (probability weighted by tie strength and partisan-identity similarity → homophily).
2. *Bounded confidence / receptivity:* Update only if opinion or identity distance < ε_i (heterogeneous threshold; Hegselmann–Krause).
3. *Argument exchange:* With probability α, exchange a randomly drawn argument from A_j on the most salient shared issue; recipient's attitude moves toward weighted argument balance (Mäs–Flache 2013).
4. *Bivalent affect update:* Affect toward out-group adjusts upward on cooperative interaction, downward on conflictual or out-party-cued interaction (Macy et al. 2003; Banisch & Olbrich 2019 reinforcement-learning route).
5. *Identity sorting:* With low rate σ, agents update one identity-axis position toward in-party modal value (modeling Mason-style sorting).
6. *Elite cue:* At each election cycle, all agents receive a noisy elite signal of party ideological position (Hetherington 2001; Levendusky 2009).
7. *Media exposure:* Each agent receives a sample of opinions weighted by media-diet partisanship (Levendusky 2013); algorithmic homophily multiplier ψ.
8. *Residential rewiring:* With low rate ρ, agents probabilistically rewire ties (or move location) preferring lifestyle-similar (and partisan-similar) others (Schelling 1971; DellaPosta, Shi & Macy 2015; Martin & Webster 2020).

**Key parameters and their predicted effects (from the literature):**

| Parameter | Range | Effect on polarization |
|---|---|---|
| Confidence threshold ε | 0–0.5 | ↓ ε → more clusters/fragmentation; ↑ ε → consensus |
| Homophily h | ≥ 0 | h ≥ ~3 → bi-polarization (Mäs–Flache 2013) |
| F (features) / q (traits) | F=5, q=2–15 | F < q → fragmentation; F > q → monoculture |
| Network modularity Q | 0–1 | Higher Q → stable bi-polarization (Banisch–Olbrich) |
| Negative-influence weight | 0–1 | > 0 produces bipolar attractor (Macy et al. 2003) |
| Identity alignment (sorting) | 0–1 | Direct linear ↑ on affective polarization (Mason 2015) |
| Electoral-system dummy | {0,1} | Majoritarian +α affective polarization (Gidron et al. 2020) |
| Elite distance Δ_elite | exogenous | + on mass sorting (Hetherington 2001) |
| Media-fragmentation φ | 0–1 | + on heavy-consumer polarization (Levendusky 2013) |
| Long-range tie fraction | 0–1 | + or − depending on whether negative influence is on (Flache & Macy 2011) |

**Stylized facts the ABM should reproduce (validation targets):**
1. Affective polarization rises faster than ideological polarization under elite-divergence + sorting shocks.
2. Sorted partisans (high identity alignment) display higher affective polarization than unsorted partisans with equal issue distance.
3. Bi-polarization (not consensus, not fragmentation) is the typical attractor in 2-party institutional settings.
4. Cross-cutting exposure can *increase* polarization when identity-threat or motivated-reasoning parameters are high (Bail et al. 2018 backfire).
5. Geographic/network homophily emerges endogenously from inadvertent + intentional sorting; pure intentional partisan sorting alone is insufficient (Martin & Webster 2020).

## Recommendations

**For an ABM-builder, staged plan:**

1. **Stage 1 — Replicate canonical models first.** Implement Deffuant, Hegselmann–Krause, Axelrod (F-q), and Flache–Macy bivalent influence as benchmarks. Confirm you can reproduce known phase diagrams (consensus/polarization/fragmentation). This anchors your work in the literature and provides a sanity layer.
2. **Stage 2 — Add a two-layer identity-attitude representation.** Following Mason and Mäs–Flache: agents have (a) a partisan identity with strength, (b) an issue vector with arguments. This is the minimum to produce affective ≠ ideological polarization. *Benchmark:* reproduce Mason's cross-cutting calm finding — sorted agents at equal issue distance show higher out-group antipathy.
3. **Stage 3 — Add network structure.** Use a small-world network with tunable modularity Q (per Banisch–Olbrich 2019) and partisan homophily in tie formation/maintenance. *Benchmark:* Bail et al. (2018) backfire condition (exposure to out-group raises polarization for some agents).
4. **Stage 4 — Add institutional/elite context.** An exogenous elite-distance time series and a media-environment parameter. *Benchmark:* Reproduce the divergence in US affective polarization trajectory vs. Germany/Sweden (Boxell, Gentzkow & Shapiro 2022).
5. **Stage 5 — Add residential/network rewiring.** Schelling-style sorting with low rate; lifestyle traits coupled to ideology (DellaPosta, Shi & Macy 2015). *Benchmark:* Endogenous geographic clustering matching Brown & Enos (2021) precinct data.

**Thresholds that would change the recommendation:**
- If the goal is *macro-historical* (e.g., 50-year US trajectory), prioritize elite-cue, media-environment, and sorting dynamics; bounded-confidence micro-rules are second-order.
- If the goal is *online-platform polarization*, prioritize network-rewiring, algorithmic exposure, and argument-pool dynamics; Schelling-style residential sorting is irrelevant.
- If the goal is *cross-national comparison*, institutional parameters (electoral system, party number) dominate; the micro-rule should be flexible.
- If empirical calibration of a single ABM to opinion data is the explicit goal, follow DellaPosta et al. (2015) and Duggins (2017) — calibrate against GSS/ANES correlation matrices.

## Caveats

1. **The literature is heavily US-centric.** Most theoretical claims are tested on US data; comparative work (Reiljan 2020; Wagner 2021; Gidron et al. 2020) is recent and CSES-bound (data start ~1996). Building an ABM "of polarization" without specifying country is suspect.

2. **Causal identification is rare.** Most polarization findings are observational; the few experiments (Bail et al. 2018; Levendusky 2013; Druckman et al. 2018) have external-validity limits (Twitter-user samples; lab settings; short durations).

3. **The "social media causes polarization" claim is empirically weaker than the public narrative.** Boxell, Gentzkow & Shapiro (*PNAS* 114(40):10612–10617, 2017) found that "our overall index and eight of the nine individual measures show greater increases for those older than 75 than for those aged 18–39," even though less than 20% of those 65+ used social media in 2012 vs. ~80% of 18–29-year-olds — undermining a simple social-media-causation story. The Meta/US 2020 Election Study suite (Guess et al. 2023, *Science*; Nyhan et al. 2023, *Nature*) finds that switching users to chronological feeds or reducing algorithmic curation produced essentially null effects on polarization over 3 months. The Reuters Institute review (Ross Arguedas et al. 2022) finds "no support for the filter bubble hypothesis."

4. **The ABM-empirical link is loose.** Most ABMs of polarization are evaluated on whether they produce qualitative patterns (consensus / bi-polarization / fragmentation); only a few (DellaPosta, Shi & Macy 2015; Duggins 2017; Banisch & Shamon's recent work; Mäs & Flache 2013) are quantitatively calibrated to opinion data. A modeler should be modest about how much "fit" justifies the model.

5. **Affective vs. ideological polarization are distinct constructs and measures.** Conflating them is a common error in popular and even some academic writing. An ABM should track them separately.

6. **Negative influence is empirically contested.** Whether real agents exhibit Macy/Flache-style repulsion is uncertain (some experiments support backfire; many show null cross-cutting effects). The Mäs–Flache (2013) argument-communication route shows bi-polarization can emerge without it — so a defensible ABM should at minimum compare the two micro-mechanisms.

7. **"Pernicious polarization" (McCoy & Somer 2019) is a regime-change construct, not a continuous measure.** Their 11-country comparative project is qualitative; quantitative cross-national affective-polarization measures (Reiljan 2020; Wagner 2021) are distinct and less politically loaded.

8. **The "Big Sort" thesis is partly disconfirmed.** Bishop (2008) overstated; Abrams & Fiorina (2012) and Martin & Webster (2020) show much residential sorting is inadvertent rather than partisan-intentional. An ABM that treats sorting as a strong intentional preference will likely over-fit.