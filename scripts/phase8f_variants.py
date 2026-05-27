"""Phase 8f variants registry. Add new experiments here."""

VARIANTS = {
    "baseline": [],

    # ---- Independents (compositional)
    "no_indep": [("build_kwarg", "independent_fraction", 0.0)],
    "indep_06": [("build_kwarg", "independent_fraction", 0.06)],

    # ---- PartyPull strength
    "pp_05": [("rule", "PartyPull", "strength", 0.05)],
    "pp_06": [("rule", "PartyPull", "strength", 0.06)],
    "pp_07": [("rule", "PartyPull", "strength", 0.07)],
    "pp_08": [("rule", "PartyPull", "strength", 0.08)],
    "pp_10": [("rule", "PartyPull", "strength", 0.10)],

    # ---- BC strength
    "bc_05": [("rule", "BoundedConfidenceInfluence", "strength", 0.05)],
    "bc_06": [("rule", "BoundedConfidenceInfluence", "strength", 0.06)],

    # ---- coupling schedules
    "coupling_high": [
        ("schedule_decade", "coupling", {
            "1980-90": 0.40, "1990-00": 0.70, "2000-10": 1.00,
            "2010-20": 1.30, "2020-25": 1.50,
        }),
    ],
    "coupling_flat_1": [
        ("schedule_decade", "coupling", {
            "1980-90": 1.0, "1990-00": 1.0, "2000-10": 1.0,
            "2010-20": 1.0, "2020-25": 1.0,
        }),
    ],
    "coupling_flat_15": [
        ("schedule_decade", "coupling", {
            "1980-90": 1.5, "1990-00": 1.5, "2000-10": 1.5,
            "2010-20": 1.5, "2020-25": 1.5,
        }),
    ],

    # ---- EliteDrift
    "elite_x2": [
        ("schedule_decade", "elite", {
            "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
            "2010-20": 0.012, "2020-25": 0.012,
        }),
    ],
    "elite_x3": [
        ("schedule_decade", "elite", {
            "1980-90": 0.0075, "1990-00": 0.0105, "2000-10": 0.0135,
            "2010-20": 0.018, "2020-25": 0.018,
        }),
    ],

    # ---- affect tweaks
    "affect_lr_half": [("rule", "AffectiveUpdate", "lr", 0.005)],
    "affect_baseline_05": [("rule", "AffectiveUpdate", "baseline", 0.05)],
    "affect_baseline_07": [("rule", "AffectiveUpdate", "baseline", 0.07)],

    # ---- IdentitySorting
    "no_id_sort": [
        ("schedule_decade", "id_sort", {
            "1980-90": 0.0, "1990-00": 0.0, "2000-10": 0.0,
            "2010-20": 0.0, "2020-25": 0.0,
        }),
    ],

    "no_party_cue": [("post_build", "strip_party_cue")],
    "no_media_cue": [("post_build", "strip_media_cue")],
    "no_media": [("rule", "MediaConsumption", "strength", 0.0)],

    # ---- combinations
    "combo_A_pp06_noind_elite2": [
        ("rule", "PartyPull", "strength", 0.06),
        ("build_kwarg", "independent_fraction", 0.0),
        ("schedule_decade", "elite", {
            "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
            "2010-20": 0.012, "2020-25": 0.012,
        }),
    ],
    "combo_B_pp06_elite2_baseline05": [
        ("rule", "PartyPull", "strength", 0.06),
        ("schedule_decade", "elite", {
            "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
            "2010-20": 0.012, "2020-25": 0.012,
        }),
        ("rule", "AffectiveUpdate", "baseline", 0.05),
    ],
    "combo_C_pp07_baseline06_elite2": [
        ("rule", "PartyPull", "strength", 0.07),
        ("rule", "AffectiveUpdate", "baseline", 0.06),
        ("schedule_decade", "elite", {
            "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
            "2010-20": 0.012, "2020-25": 0.012,
        }),
    ],
    "combo_D_pp08_baseline05_elite2_couphi": [
        ("rule", "PartyPull", "strength", 0.08),
        ("rule", "AffectiveUpdate", "baseline", 0.05),
        ("schedule_decade", "elite", {
            "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
            "2010-20": 0.012, "2020-25": 0.012,
        }),
        ("schedule_decade", "coupling", {
            "1980-90": 0.40, "1990-00": 0.70, "2000-10": 1.00,
            "2010-20": 1.30, "2020-25": 1.50,
        }),
    ],
}

# y-axis sort test
VARIANTS["y_sort"] = [("post_build", "add_y_axis_sort")]
VARIANTS["combo_E_pp06_elite2_ysort"] = [
    ("rule", "PartyPull", "strength", 0.06),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
        "2010-20": 0.012, "2020-25": 0.012,
    }),
    ("post_build", "add_y_axis_sort"),
]
VARIANTS["combo_F_pp06_elite2_ysort_baseline05"] = [
    ("rule", "PartyPull", "strength", 0.06),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
        "2010-20": 0.012, "2020-25": 0.012,
    }),
    ("post_build", "add_y_axis_sort"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]

VARIANTS["combo_G_pp06_elite2_ysort10"] = [
    ("rule", "PartyPull", "strength", 0.06),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.007, "2000-10": 0.009,
        "2010-20": 0.012, "2020-25": 0.012,
    }),
    ("post_build", "add_y_axis_sort_10"),
]
VARIANTS["combo_H_pp05_ysort10_baseline05"] = [
    ("rule", "PartyPull", "strength", 0.05),
    ("post_build", "add_y_axis_sort_10"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_I_pp06_ysort15_baseline05"] = [
    ("rule", "PartyPull", "strength", 0.06),
    ("post_build", "add_y_axis_sort_15"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_J_pp06_ysort08_baseline05"] = [
    ("rule", "PartyPull", "strength", 0.06),
    ("post_build", "add_y_axis_sort_08"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["y_sort_only_10"] = [("post_build", "add_y_axis_sort_10")]
VARIANTS["y_sort_only_15"] = [("post_build", "add_y_axis_sort_15")]

VARIANTS["combo_K_ysort10_pp06"] = [
    ("post_build", "add_y_axis_sort_10"),
    ("rule", "PartyPull", "strength", 0.06),
]
VARIANTS["combo_L_ysort10_pp06_baseline05"] = [
    ("post_build", "add_y_axis_sort_10"),
    ("rule", "PartyPull", "strength", 0.06),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_M_ysort10_pp05_baseline05"] = [
    ("post_build", "add_y_axis_sort_10"),
    ("rule", "PartyPull", "strength", 0.05),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_N_ysort10_pp07_baseline05"] = [
    ("post_build", "add_y_axis_sort_10"),
    ("rule", "PartyPull", "strength", 0.07),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_O_ysort10_baseline05"] = [
    ("post_build", "add_y_axis_sort_10"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]

VARIANTS["combo_P_ysort08_pp07_baseline05"] = [
    ("post_build", "add_y_axis_sort_08"),
    ("rule", "PartyPull", "strength", 0.07),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_Q_ysort08_pp06_baseline05"] = [
    ("post_build", "add_y_axis_sort_08"),
    ("rule", "PartyPull", "strength", 0.06),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["y_sort_only_08"] = [("post_build", "add_y_axis_sort_08")]

VARIANTS["pc_05"] = [("post_build", "bump_party_cue_05")]
VARIANTS["pc_07"] = [("post_build", "bump_party_cue_07")]
VARIANTS["mc_30"] = [("post_build", "bump_media_cue_30")]
VARIANTS["pc_05_mc_30"] = [
    ("post_build", "bump_party_cue_05"),
    ("post_build", "bump_media_cue_30"),
]

VARIANTS["mc_40"] = [("post_build", "bump_media_cue_40")]
VARIANTS["mc_50"] = [("post_build", "bump_media_cue_50")]

VARIANTS["combo_R_pp07_ysort08_mc30_b05"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_30"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_S_pp08_ysort10_mc30_b05"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_30"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_T_pp08_ysort10_mc40_b05"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]
VARIANTS["combo_U_pp08_ysort15_mc40_b05"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_15"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.05),
]

VARIANTS["combo_V_pp08_ysort10_mc40_b03"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
]
VARIANTS["combo_W_pp08_ysort10_mc40_b07"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.07),
]

VARIANTS["combo_X_pp08_ysort10_mc40_b03_elite15"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]
VARIANTS["combo_Y_pp10_ysort10_mc40_b03"] = [
    ("rule", "PartyPull", "strength", 0.10),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
]
VARIANTS["combo_Z_pp08_ysort12_mc40_b03"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_10"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
    ("schedule_decade", "coupling", {
        "1980-90": 0.60, "1990-00": 0.85, "2000-10": 1.05,
        "2010-20": 1.15, "2020-25": 1.20,
    }),
]

VARIANTS["combo_AA_pp08_ysort09_mc40_b03_elite15"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_09"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]
VARIANTS["combo_BB_pp08_ysort08_mc40_b03_elite15"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]
VARIANTS["combo_CC_pp07_ysort08_mc40_b03_elite15"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]

VARIANTS["combo_DD_pp07_ysort08_mc40_b01_elite15"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.01),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]
VARIANTS["combo_EE_pp08_ysort09_mc40_b03_elite15"] = [
    ("rule", "PartyPull", "strength", 0.08),
    ("post_build", "add_y_axis_sort_09"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.03),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]

VARIANTS["combo_FF_pp07_ysort08_mc40_b01_elite_early"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.01),
    ("schedule_decade", "elite", {
        "1980-90": 0.006, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]
VARIANTS["combo_GG_pp075_ysort08_mc40_b02_elite15"] = [
    ("rule", "PartyPull", "strength", 0.075),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.02),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.006, "2000-10": 0.007,
        "2010-20": 0.008, "2020-25": 0.008,
    }),
]

VARIANTS["combo_HH"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.01),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.006, "2020-25": 0.005,
    }),
]
VARIANTS["combo_II"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.02),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]

# Time-varying affect baseline: cool faster early, slower mid
VARIANTS["combo_JJ"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.0),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]
# raise media_cue even further to lift wp_sd
VARIANTS["combo_KK"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_50"),
    ("rule", "AffectiveUpdate", "baseline", 0.02),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]

# Ablations of combo_JJ (drop one component at a time)
VARIANTS["abl_no_pp07"] = [
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.0),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]
VARIANTS["abl_no_ysort08"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.0),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]
VARIANTS["abl_no_mc40"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("rule", "AffectiveUpdate", "baseline", 0.0),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]
VARIANTS["abl_no_baseline0"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("schedule_decade", "elite", {
        "1980-90": 0.005, "1990-00": 0.008, "2000-10": 0.008,
        "2010-20": 0.007, "2020-25": 0.006,
    }),
]
VARIANTS["abl_no_elite"] = [
    ("rule", "PartyPull", "strength", 0.07),
    ("post_build", "add_y_axis_sort_08"),
    ("post_build", "bump_media_cue_40"),
    ("rule", "AffectiveUpdate", "baseline", 0.0),
]
