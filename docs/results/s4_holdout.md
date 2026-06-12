# MHV S4 T4.4 -- holdout battery scorecard

**Overall: PASS** (3/3 substantive cuts pass; power-band rule: >=2/3). Bands pre-registered in s4_targets.py before the fit.

| cut | verdict |
|---|---|
| cut1_temporal | PASS |
| cut2_instrument | PASS |
| cut3_statistic | PASS |

## Cut 1 -- temporal (fit <=2012 -> predict 2010/2020/2025)
refit point: party_pull=0.181, fj_alpha_scale=2.349, constraint_rate=0.033, animus_mult=0.664, noise_sigma=0.048, elite_lead=1.771

| decade.metric | pred band (8 seeds) | widened ANES band | in? |
|---|---|---|---|
| 2010.party_sep | [0.684,0.886] | [0.72,1.0] | OK |
| 2010.affect | [-0.516,-0.448] | [-0.58,-0.34] | OK |
| 2010.constraint | [0.625,0.734] | [0.51,0.79] | OK |
| 2010.within_party_sd | [0.269,0.327] | [0.19,0.47] | OK |
| 2020.party_sep | [0.886,1.069] | [0.97,1.25] | OK |
| 2020.affect | [-0.633,-0.549] | [-0.73,-0.49] | OK |
| 2020.constraint | [0.760,0.823] | [0.6,0.87] | OK |
| 2020.within_party_sd | [0.238,0.271] | [0.21,0.48] | OK |
| 2025.party_sep | [0.869,1.044] | [1.01,1.29] | OK |
| 2025.affect | [-0.666,-0.584] | [-0.78,-0.44] | OK |
| 2025.constraint | [0.753,0.813] | [0.62,0.89] | OK |
| 2025.within_party_sd | [0.241,0.274] | [0.21,0.48] | OK |

## Cut 2 -- instrument (shipped model -> held-out GSS trends)
| trend | engine slope/yr | GSS slope/yr | within +/-50% & sign? |
|---|---|---|---|
| partisan align (bg) | +0.01104 | +0.00851 | OK |
| issue |corr| (constraint_index) | +0.00807 | +0.00568 | OK |

## Cut 3 -- statistic (fit sep/affect/wp_sd -> predict constraint)
refit point: party_pull=0.306, fj_alpha_scale=2.204, constraint_rate=0.036, animus_mult=0.651, noise_sigma=0.047, elite_lead=1.758

| decade | pred constraint band | widened ANES constraint | in? |
|---|---|---|---|
| 1980 | [0.194,0.454] | [0.2,0.48] | OK |
| 1990 | [0.348,0.550] | [0.3,0.58] | OK |
| 2000 | [0.455,0.625] | [0.39,0.67] | OK |
| 2010 | [0.610,0.721] | [0.51,0.79] | OK |
| 2020 | [0.761,0.822] | [0.6,0.87] | OK |
| 2025 | [0.742,0.817] | [0.62,0.89] | OK |