"""Chain Conveyor Calculator — one-page engineering application.

Version based on public main branch inspected on 2026-11-04.
Static images are reused from the existing repository's assets/ directory.
"""
from __future__ import annotations

from html import escape
from math import pi
from pathlib import Path

import pandas as pd
import streamlit as st

from src.calculations import (
    CompleteGearmotorInput,
    DriveOutput,
    ConveyorInput,
    SecondaryTransmissionInput,
    SeparateDriveInput,
    calculate_conveyor,
    calculate_final_output,
    calculate_secondary_requirement,
    complete_gearmotor_output,
    cv_to_kw,
    cylindrical_mass,
    kw_to_cv,
    rectangular_mass,
    separate_drive_output,
)
from src.ibr_catalog import (
    RATIOS,
    SIZES,
    evaluate_ibr_q,
    get_ibr_q,
    catalogue_radial_force,
    required_service_factor,
)

st.set_page_config(
    page_title="Chain Conveyor Calculator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def find_asset(stem: str) -> Path | None:
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        path = ASSETS_DIR / f"{stem}{extension}"
        if path.is_file():
            return path
    if ASSETS_DIR.exists():
        for path in ASSETS_DIR.iterdir():
            if path.is_file() and path.stem.casefold() == stem.casefold() \
                    and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                return path
    return None


IMG_RETURN = find_asset("return")
IMG_SAG = find_asset("sag")
IMG_DIRECT = find_asset("direct")
IMG_REDUCTION = find_asset("reduction")
IMG_PRISM = find_asset("auxiliary prism")
IMG_CYLINDER = find_asset("auxiliary cylinder")

st.markdown(
    """<style>
    :root { --border:#d9dde4; --header:#eaf2f8; --muted:#667085;
      --ok-bg:#ecfdf3; --ok-fg:#067647; --warn-bg:#fff7ed;
      --warn-fg:#b54708; --bad-bg:#fef3f2; --bad-fg:#b42318; }
    .block-container {max-width:1500px; padding:0.75rem 1rem 1.5rem;}
    header[data-testid="stHeader"] {height:2rem;}
    h1 {font-size:1.38rem!important;line-height:1.15!important;margin:0!important;}
    .section-bar {background:var(--header);border:1px solid var(--border);
      border-radius:5px;padding:.38rem .52rem;margin:.55rem 0 .35rem;
      font-size:.94rem;line-height:1.2rem;font-weight:700;clear:both;}
    .cell-grid {display:grid;border-top:1px solid var(--border);
      border-left:1px solid var(--border);margin-bottom:.3rem;}
    .cell {border-bottom:1px solid var(--border);border-right:1px solid var(--border);
      padding:.34rem .46rem;min-height:52px;min-width:0;background:white;}
    .cell-label {font-size:.78rem;color:var(--muted);line-height:1.04rem;}
    .cell-value {font-size:1rem;font-weight:700;color:#1f2937;
      line-height:1.1rem;margin-top:.06rem;overflow-wrap:anywhere;}
    .status-ok,.status-warn,.status-bad {display:inline-block;border-radius:4px;
      font-size:.76rem;font-weight:700;padding:.08rem .28rem;}
    .status-ok {background:var(--ok-bg);color:var(--ok-fg);}
    .status-warn {background:var(--warn-bg);color:var(--warn-fg);}
    .status-bad {background:var(--bad-bg);color:var(--bad-fg);}
    .tiny-caption {font-size:.78rem;color:var(--muted);margin-top:.1rem;}
    .app-note {font-size:.88rem;color:#344054;}
    div[data-testid="stVerticalBlock"] {gap:.32rem;}
    div[data-testid="stHorizontalBlock"] {gap:.52rem;align-items:flex-start;}
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stToggle"] label {font-size:.76rem!important;
      line-height:.90rem!important;margin-bottom:.05rem!important;}
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {font-size:.86rem!important;
      height:2.18rem!important;min-height:2.18rem!important;
      padding-top:.16rem!important;padding-bottom:.16rem!important;
      background:#f4f6f8!important;}
    div[data-testid="stSelectbox"] > div > div {min-height:2.18rem!important;
      font-size:.86rem!important;background:#f4f6f8!important;}
    div[data-testid="stExpander"] summary {font-size:.82rem!important;font-weight:600!important;}
    .power-label {font-size:.76rem;margin-bottom:.1rem;}
    .schematic-image img {max-height:320px;object-fit:contain;}
    .panel-note {border:1px solid var(--border);padding:.4rem .5rem;
      color:var(--muted);font-size:.82rem;line-height:1.25rem;}
    @media(max-width:900px) {
      .block-container {padding:.45rem .55rem 1rem;}
      .cell-grid {grid-template-columns:repeat(2,minmax(0,1fr))!important;}
      .section-bar {margin-top:.25rem;}
    }
    </style>""",
    unsafe_allow_html=True,
)


def fmt(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}"


def section_bar(title: str) -> None:
    st.markdown(f'<div class="section-bar">{escape(title)}</div>', unsafe_allow_html=True)


def cell_grid(items: list[tuple[str, str]], columns: int = 2) -> None:
    cols = " ".join("minmax(0,1fr)" for _ in range(columns))
    parts = [f'<div class="cell-grid" style="grid-template-columns:{cols}">']
    for label, value in items:
        parts.append(f'<div class="cell"><div class="cell-label">{escape(label)}</div>'
                     f'<div class="cell-value">{escape(value)}</div></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {"OK": "status-ok", "WARNING": "status-warn",
           "REVIEW": "status-warn", "FAIL": "status-bad"}.get(status, "status-warn")
    return f'<span class="{cls}">{escape(status)}</span>'


def capacity_status(available: float, required: float) -> tuple[float, str]:
    if required <= 0:
        return 0.0, "REVIEW"
    ratio = available / required
    return ratio, "OK" if ratio >= 1.2 else "WARNING" if ratio >= 1 else "FAIL"


def speed_status(available: float, required: float) -> tuple[float, str]:
    if required <= 0:
        return 0.0, "REVIEW"
    error = (available - required) / required
    return error, "OK" if abs(error) <= 0.05 else "REVIEW"


def render_schematic(path: Path | None, missing_text: str) -> None:
    if path is None:
        st.warning(missing_text)
    else:
        st.image(str(path), use_container_width=True)


def power_from_kw(prefix: str) -> None:
    st.session_state[f"{prefix}_cv"] = kw_to_cv(st.session_state[f"{prefix}_kw"])


def power_from_cv(prefix: str) -> None:
    st.session_state[f"{prefix}_kw"] = cv_to_kw(st.session_state[f"{prefix}_cv"])


def motor_power_pair(prefix: str, default_kw: float) -> float:
    """Two editable Streamlit widgets with last-edited-unit winning."""
    key_kw = f"{prefix}_kw"
    key_cv = f"{prefix}_cv"
    if key_kw not in st.session_state:
        st.session_state[key_kw] = default_kw
    if key_cv not in st.session_state:
        st.session_state[key_cv] = kw_to_cv(st.session_state[key_kw])
    st.markdown('<div class="power-label">Motor rated power</div>', unsafe_allow_html=True)
    a, b = st.columns(2, gap="small")
    with a:
        st.number_input("kW", key=key_kw, min_value=0.0,
                        step=0.1, format="%.3f", on_change=power_from_kw, args=(prefix,))
    with b:
        st.number_input("cv", key=key_cv, min_value=0.0,
                        step=0.1, format="%.3f", on_change=power_from_cv, args=(prefix,))
    return float(st.session_state[key_kw])


def _reset_ibr_catalog_motor() -> None:
    """Restore the corresponding catalog maximum commercial motor when the row changes."""
    if "ibr_size" in st.session_state and "ibr_ratio" in st.session_state:
        cv = get_ibr_q(st.session_state["ibr_size"], st.session_state["ibr_ratio"]).catalogue_motor_cv
        st.session_state["ibr_motor_cv"] = cv
        st.session_state["ibr_motor_kw"] = cv_to_kw(cv)


st.title("Chain Conveyor Calculator")
st.markdown('<div class="app-note">System demand · drive selection · required vs available</div>',
            unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1 — SYSTEM INPUTS
# -----------------------------------------------------------------------------
col_sys, col_scheme = st.columns([1.15, .85], gap="medium")
with col_sys:
    section_bar("1 · SYSTEM INPUTS")
    r = st.columns(3)
    with r[0]:
        center_distance_m = st.number_input("Center distance C [m]", min_value=.01,
                                            value=4.15554, step=.1)
    with r[1]:
        conveyor_dp = st.number_input("Pitch diameter Dp [mm]", min_value=1.,
                                      value=260., step=1.)
    with r[2]:
        use_inclination = st.toggle("Inclination", value=False)
        inclination_deg = st.number_input("α [°]", value=0., step=1.) if use_inclination else 0.

    r = st.columns(2)
    with r[0]:
        return_mode = st.selectbox("Return type", ["Guided return", "Sag return"])
    with r[1]:
        if return_mode == "Guided return":
            mu_return = st.number_input("Return friction μ_ret [-]", min_value=0.,
                                        value=.25, step=.01)
            sag_mm, internal_return_type = 80., "Guiado"
        else:
            sag_mm = st.number_input("Return sag s [mm]", min_value=1.,
                                     value=80., step=5.)
            mu_return, internal_return_type = 0., "Livre"

    r = st.columns(3)
    with r[0]:
        strands = st.number_input("Chain strands [-]", min_value=1, value=4, step=1)
    with r[1]:
        chain_mass_per_m = st.number_input("Chain mass [kg/m]", min_value=.01,
                                            value=7.30, step=.10,
                                            help="Mass per metre for ONE complete chain strand, including its width/configuration.")
    with r[2]:
        mu_top = st.number_input("Top friction μ_top [-]", min_value=0.,
                                 value=.35, step=.01)
    mass_breakdown_slot = st.empty()

    r = st.columns(3)
    with r[0]:
        load_mass = st.number_input("Carried load [kg]", min_value=.01, value=276., step=10.)
    with r[1]:
        additional_force = st.number_input("Additional F_add [N]", min_value=0.,
                                           value=0., step=10.)
    with r[2]:
        linear_speed = st.number_input("Desired speed [m/min]", min_value=.01,
                                       value=35., step=1.)

    r = st.columns(3)
    with r[0]:
        consider_acceleration = st.toggle("Acceleration", value=True)
    with r[1]:
        acceleration_time = (st.number_input("Acceleration time [s]", min_value=.01,
                                             value=3., step=.5)
                             if consider_acceleration else 0.)
    with r[2]:
        design_factor = st.number_input("Drive design factor [-]", min_value=1.,
                                        value=1.5, step=.05,
                                        help="Applied ONCE to force, torque and power demand; not the chain breaking-load factor or a catalog gearmotor service factor.")

conveyor = calculate_conveyor(ConveyorInput(
    center_distance_m=center_distance_m,
    strands=int(strands),
    chain_mass_per_m_kg=chain_mass_per_m,
    inclination_deg=inclination_deg,
    conveyor_sprocket_pitch_diameter_mm=conveyor_dp,
    return_type=internal_return_type,
    return_sag_mm=sag_mm,
    mu_top=mu_top,
    mu_return=mu_return,
    load_mass_kg=load_mass,
    linear_speed_m_min=linear_speed,
    additional_process_force_n=additional_force,
    acceleration_time_s=acceleration_time,
    design_factor=design_factor,
))

with mass_breakdown_slot.container():
    cell_grid([
        ("Top chains", f"{fmt(conveyor.top_chain_mass_kg,1)} kg"),
        ("Return chains", f"{fmt(conveyor.return_chain_mass_kg,1)} kg"),
        ("Sprocket wraps", f"{fmt(conveyor.arc_chain_mass_kg,1)} kg"),
        ("Total chain mass", f"{fmt(conveyor.total_chain_mass_kg,1)} kg"),
    ], columns=4)

with col_scheme:
    section_bar("SYSTEM SCHEMATIC")
    render_schematic(IMG_RETURN if return_mode == "Guided return" else IMG_SAG,
                     "Return schematic image not found in assets/.")
    st.markdown('<div class="tiny-caption">Static illustrative schematic · calculated values below</div>',
                unsafe_allow_html=True)

section_bar("SYSTEM DEMAND")
demand_items = [
    ("Design force", f"{fmt(conveyor.design_force_n,0)} N"),
    ("Force / strand", f"{fmt(conveyor.force_per_strand_n,0)} N"),
    ("Shaft torque", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m"),
    ("Power", f"{fmt(conveyor.required_axis_power_kw,2)} kW"),
    ("Power", f"{fmt(conveyor.required_axis_power_cv,2)} cv"),
    ("Shaft speed", f"{fmt(conveyor.required_axis_speed_rpm,1)} rpm"),
    ("Top supported mass", f"{fmt(conveyor.top_supported_mass_kg,1)} kg"),
    ("Total chain mass", f"{fmt(conveyor.total_chain_mass_kg,1)} kg"),
    ("Top friction F_top", f"{fmt(conveyor.top_friction_n,0)} N"),
    ("Return friction F_ret", f"{fmt(conveyor.return_friction_n,0)} N"),
    ("Steady resistance", f"{fmt(conveyor.regime_force_n,0)} N"),
]
if consider_acceleration:
    demand_items.extend([
        ("Acceleration", f"{fmt(conveyor.acceleration_m_s2,3)} m/s²"),
        ("Acceleration force", f"{fmt(conveyor.acceleration_force_n,0)} N"),
    ])
cell_grid(demand_items, columns=5)

# -----------------------------------------------------------------------------
# 2 — DRIVE CONNECTION
# -----------------------------------------------------------------------------
col_conn_input, col_conn_img = st.columns([.95, 1.05], gap="medium")
with col_conn_input:
    section_bar("2 · DRIVE CONNECTION")
    coupling_mode = st.radio("Connection", ["Direct", "Secondary chain transmission"],
                             horizontal=True)
    if coupling_mode == "Secondary chain transmission":
        internal_coupling = "Transmissão secundária"
        r = st.columns(3)
        with r[0]:
            secondary_dp1 = st.number_input("Dp1 [mm]", min_value=1., value=170., step=1.)
        with r[1]:
            secondary_dp2 = st.number_input("Dp2 [mm]", min_value=1., value=202.66, step=1.)
        with r[2]:
            secondary_eff = st.number_input("η_sec [%]", min_value=1., max_value=100.,
                                            value=98., step=.5)
    else:
        internal_coupling = "Direto"
        secondary_dp1, secondary_dp2, secondary_eff = 1., 1., 100.

transmission = SecondaryTransmissionInput(
    coupling_type=internal_coupling,
    reducer_sprocket_pitch_diameter_mm=secondary_dp1,
    shaft_sprocket_pitch_diameter_mm=secondary_dp2,
    efficiency_pct=secondary_eff,
)
requirement = calculate_secondary_requirement(
    conveyor.required_axis_speed_rpm,
    conveyor.required_axis_torque_nm,
    conveyor.required_axis_power_kw,
    transmission,
)
with col_conn_input:
    cell_grid([
        ("Req. reducer speed", f"{fmt(requirement.required_reducer_speed_rpm,1)} rpm"),
        ("Req. reducer torque", f"{fmt(requirement.required_reducer_torque_nm,1)} N·m"),
        ("Req. reducer power", f"{fmt(requirement.required_reducer_power_kw,2)} kW"),
    ], columns=1)
with col_conn_img:
    section_bar("DRIVE SCHEMATIC")
    render_schematic(IMG_DIRECT if coupling_mode == "Direct" else IMG_REDUCTION,
                     "Drive schematic image not found in assets/.")
    st.markdown('<div class="tiny-caption">Static illustrative schematic</div>',
                unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3 — PROVIDED DRIVE
# -----------------------------------------------------------------------------
col_drive, col_compare = st.columns([1.25, .75], gap="medium")
with col_drive:
    section_bar("3 · PROVIDED DRIVE")
    supply_mode = st.radio(
        "Supply mode",
        ["IBR Q catalogue", "Complete gearmotor", "Separate gearbox + motor"],
        horizontal=True,
        index=0,
    )
    ibr_row = None
    ibr_perf = None
    ibr_required_fs = None
    ibr_radial_catalogue = None
    if supply_mode == "IBR Q catalogue":
        st.caption("IBR Q worm gearbox · transcribed selection table, printed catalogue p.13–14 · "
                   "frame sizes 075–150; ratios 30, 40 and 50 only. Not the full product range.")
        r1 = st.columns([1, 1, 2, 1])
        with r1[0]:
            ibr_size = st.selectbox("IBR Q frame", SIZES, index=1,
                                    key="ibr_size", on_change=_reset_ibr_catalog_motor)
        with r1[1]:
            ibr_ratio = st.selectbox("Ratio i [-]", RATIOS, index=1,
                                     key="ibr_ratio", on_change=_reset_ibr_catalog_motor)
        ibr_row = get_ibr_q(ibr_size, ibr_ratio)
        with r1[2]:
            ibr_motor_kw = motor_power_pair("ibr_motor", cv_to_kw(ibr_row.catalogue_motor_cv))
        with r1[3]:
            ibr_motor_rpm = st.number_input("Motor rpm", min_value=1.0,
                                           value=1700.0, step=10.0, key="ibr_motor_rpm")
        ibr_perf = evaluate_ibr_q(ibr_row, kw_to_cv(ibr_motor_kw), ibr_motor_rpm)
        r2 = st.columns(3)
        with r2[0]:
            ibr_starts = st.selectbox("Starts / hour", ["<10", ">10"], index=0)
        with r2[1]:
            ibr_duty = st.selectbox("Load classification", ["Uniform load", "Moderate shocks", "Severe shocks"], index=1)
        with r2[2]:
            ibr_hours = st.selectbox("Operation [hours/day]", ["<2", "2–10", ">10"], index=1)
        ibr_required_fs = required_service_factor(ibr_starts, ibr_duty, ibr_hours)
        ibr_service_status = ("OK" if ibr_perf.service_factor_motor >= ibr_required_fs - 1e-6
                              else "REVIEW")
        # Actual-demand diagnostic: base includes acceleration, excludes the explicit design factor.
        ibr_base_torque = requirement.required_reducer_torque_nm / design_factor
        ibr_effective_fs_base = (ibr_row.nominal_torque_nm / ibr_base_torque
                                 if ibr_base_torque > 0 else float('inf'))
        ibr_effective_fs_design = (ibr_row.nominal_torque_nm / requirement.required_reducer_torque_nm
                                   if requirement.required_reducer_torque_nm > 0 else float('inf'))
        cell_grid([
            ("Catalog PMot limit", f"{fmt(ibr_row.catalogue_motor_cv,2)} cv"),
            ("M2M with entered motor", f"{fmt(ibr_perf.output_torque_nm,1)} N·m"),
            ("M2Nom (catalog)", f"{fmt(ibr_row.nominal_torque_nm,0)} N·m"),
            ("η gearbox", f"{fmt(ibr_row.efficiency_pct,0)} %"),
            ("Catalog fs at motor rating", f"{fmt(ibr_perf.service_factor_motor,2)} ({ibr_service_status})"),
            ("Required fs by duty", f"{fmt(ibr_required_fs,2)}"),
            ("fs / calculated base load", f"{fmt(ibr_effective_fs_base,2)}"),
            ("M2Nom / design torque", f"{fmt(ibr_effective_fs_design,2)}"),
            ("Admissible output FR2", f"{fmt(ibr_row.admissible_radial_output_n,0)} N"),
            ("Catalog PNom", f"{fmt(ibr_row.nominal_input_cv,2)} cv"),
        ], columns=4)
        if not (ibr_perf.within_catalogue_motor_limit and ibr_perf.within_nominal_input_limit
                and ibr_perf.within_nominal_torque_limit):
            st.error("Entered motor exceeds a catalog limit. Select a smaller motor or a larger gearbox.")
        if ibr_service_status != "OK":
            st.warning("The catalog service factor at the motor's full rated torque is below the "
                       "selected duty-table target. The effective factor relative to the actual "
                       "calculated base load may be higher, because the motor is not fully loaded. "
                       "The application design factor is already included in required torque. "
                       "Do not combine margins silently; confirm selection criterion with IBR.")
        if coupling_mode == "Secondary chain transmission":
            st.caption("IBR radial-force screening for a secondary chain: "
                       "FR ≈ 2000 × M2M × 1.25 × p / Dp1; p depends on the force application point.")
            ibr_p = st.selectbox("Application-point factor p", [1.0, 1.5], index=0,
                                 help="Catalog p=1 or 1.5 depends on force application distance relative "
                                      "to output shaft length. Verify actual load point; do not assume p=1.")
            ibr_radial_catalogue = catalogue_radial_force(
                ibr_perf.output_torque_nm, secondary_dp1, 1.25, ibr_p)
            _, radial_catalogue_status = capacity_status(
                ibr_row.admissible_radial_output_n, ibr_radial_catalogue)
            cell_grid([
                ("IBR estimated FR at rated motor", f"{fmt(ibr_radial_catalogue,0)} N"),
                ("IBR admissible FR2", f"{fmt(ibr_row.admissible_radial_output_n,0)} N"),
                ("Catalog radial screening", "PASS" if ibr_radial_catalogue <= ibr_row.admissible_radial_output_n else "FAIL"),
            ], columns=3)
            st.caption("This is the IBR catalog's simplified radial load estimate at the selected motor rating. "
                       "It does not replace the chain branch-tension vector model; final radial status remains REVIEW.")
        st.caption("Catalog uses n1=1700 rpm (4-pole reference). Actual selected motor rpm changes output speed "
                   "and calculated M2M; the efficiency and torque limit are held at catalog values as an approximation.")
        if coupling_mode == "Direct":
            with st.expander("IBR Q alternatives at this ratio and chosen motor power"):
                alternatives = []
                for size in SIZES:
                    alt_row = get_ibr_q(size, ibr_ratio)
                    alt_motor_cv = min(ibr_perf.motor_power_cv, alt_row.catalogue_motor_cv)
                    alt_perf = evaluate_ibr_q(alt_row, alt_motor_cv, ibr_motor_rpm)
                    alt_speed = pi * (conveyor_dp / 1000.0) * alt_perf.output_rpm
                    speed_ok = abs(alt_speed / linear_speed - 1.0) <= .05
                    torque_ok = alt_perf.output_torque_nm >= conveyor.required_axis_torque_nm
                    power_ok = alt_perf.output_power_kw >= conveyor.required_axis_power_kw
                    fs_ok = alt_perf.service_factor_motor >= ibr_required_fs
                    alt_status = "PASS*" if speed_ok and torque_ok and power_ok and fs_ok else "REVIEW"
                    alternatives.append({
                        "Model": f"IBR Q{size}", "i": f"{ibr_ratio:g}",
                        "Motor [cv]": round(alt_motor_cv, 2),
                        "Speed [m/min]": round(alt_speed, 2),
                        "M2M [N·m]": round(alt_perf.output_torque_nm, 1),
                        "M2Nom [N·m]": round(alt_row.nominal_torque_nm),
                        "fs with motor": round(alt_perf.service_factor_motor, 2),
                        "fs required": ibr_required_fs,
                        "FR2 [N]": round(alt_row.admissible_radial_output_n),
                        "Preliminary": alt_status,
                    })
                st.dataframe(pd.DataFrame(alternatives), hide_index=True, use_container_width=True)
                st.caption("*PASS is preliminary numerical screening only; verify thermal limit, "
                           "manufacturer selection, mounting and actual service regime. "
                           "Motor power is limited to the smaller of the currently entered motor "
                           "power or each catalog row's PMot maximum. "
                           "The design factor is already included in required torque/power.")
        effective_torque = min(ibr_perf.output_torque_nm, ibr_row.nominal_torque_nm)
        effective_power = effective_torque * 2 * pi * ibr_perf.output_rpm / 60 / 1000
        drive = DriveOutput(
            reducer_output_speed_rpm=ibr_perf.output_rpm,
            reducer_output_torque_nm=effective_torque,
            reducer_output_power_kw=effective_power,
            admissible_radial_force_n=ibr_row.admissible_radial_output_n,
        )
    elif supply_mode == "Complete gearmotor":
        r1 = st.columns([1, 1, 2, 1])
        with r1[0]:
            gm_manufacturer = st.text_input("Manufacturer", "SEW-EURODRIVE")
        with r1[1]:
            gm_model = st.text_input("Model", "")
        with r1[2]:
            gm_motor_power = motor_power_pair("gearmotor", 15.0)
        with r1[3]:
            gm_motor_speed = st.number_input("Motor rpm", min_value=.01,
                                             value=1777., step=1.)
        r2 = st.columns(4)
        with r2[0]:
            gm_ratio = st.number_input("Ratio", min_value=.001, value=22.37, step=.01)
        with r2[1]:
            gm_output_speed = st.number_input("Output rpm", min_value=.01,
                                              value=79., step=1.)
        with r2[2]:
            gm_output_torque = st.number_input("Output N·m", min_value=.01,
                                               value=1790., step=10.)
        with r2[3]:
            gm_radial = st.number_input("Radial limit [N]", min_value=0.,
                                        value=15600., step=100.)
        gm_service_factor = st.number_input(
            "Manufacturer service factor [-]", min_value=0., value=1.50, step=.05,
            help="Catalog factor (manufacturer-specific). Shown for reference; it is NOT a multiplier on available power or torque.",
        )
        drive = complete_gearmotor_output(CompleteGearmotorInput(
            manufacturer=gm_manufacturer, model=gm_model,
            motor_power_kw=gm_motor_power, motor_speed_rpm=gm_motor_speed,
            output_speed_rpm=gm_output_speed, total_ratio=gm_ratio,
            output_torque_nm=gm_output_torque, admissible_radial_force_n=gm_radial,
            manufacturer_service_factor=gm_service_factor,
        ))
    else:
        section_bar("GEARBOX")
        r1 = st.columns(4)
        with r1[0]:
            reducer_manufacturer = st.text_input("Gearbox mfr.", "Geremia")
        with r1[1]:
            reducer_model = st.text_input("Gearbox model", "GD30/2R")
        with r1[2]:
            reducer_ratio = st.number_input("Gear ratio", min_value=.001,
                                             value=35., step=.01)
        with r1[3]:
            reducer_eff = st.number_input("Gear η [%]", min_value=.01,
                                          max_value=100., value=96., step=.5)
        r2 = st.columns(3)
        with r2[0]:
            reducer_max_torque = st.number_input("Max torque [N·m]", min_value=0.,
                                                 value=370., step=10.)
        with r2[1]:
            reducer_radial = st.number_input("Radial limit [N]", min_value=0.,
                                             value=6300., step=100.)
        with r2[2]:
            reducer_max_power = st.number_input("Max input [kW]", min_value=0.,
                                                value=1.50, step=.10)
        section_bar("MOTOR")
        r3 = st.columns([1, 1, 2, 1])
        with r3[0]:
            motor_manufacturer = st.text_input("Motor mfr.", "WEG")
        with r3[1]:
            motor_model = st.text_input("Motor model", "")
        with r3[2]:
            motor_power = motor_power_pair("separate_motor", 1.50)
        with r3[3]:
            motor_speed = st.number_input("Motor rpm", min_value=.01,
                                          value=1745., step=1.)
        r4 = st.columns(3)
        with r4[0]:
            motor_eff = st.number_input("Motor η [%]", min_value=.01,
                                        max_value=100., value=86.5, step=.1)
        with r4[1]:
            nominal_freq = st.number_input("Rated Hz", min_value=.01,
                                           value=60., step=1.)
        with r4[2]:
            operating_freq = st.number_input("Operating Hz", min_value=.01,
                                             value=60., step=1.)
        drive = separate_drive_output(SeparateDriveInput(
            reducer_manufacturer=reducer_manufacturer, reducer_model=reducer_model,
            reducer_ratio=reducer_ratio, reducer_efficiency_pct=reducer_eff,
            reducer_max_torque_nm=reducer_max_torque,
            reducer_admissible_radial_force_n=reducer_radial,
            reducer_max_input_power_kw=reducer_max_power,
            motor_manufacturer=motor_manufacturer, motor_model=motor_model,
            motor_power_kw=motor_power, motor_speed_rpm=motor_speed,
            motor_efficiency_pct=motor_eff, nominal_frequency_hz=nominal_freq,
            operating_frequency_hz=operating_freq,
        ))

final_output = calculate_final_output(drive, transmission, conveyor_dp)

# -----------------------------------------------------------------------------
# 4 — REQUIRED VS AVAILABLE
# -----------------------------------------------------------------------------
with col_compare:
    section_bar("4 · REQUIRED × AVAILABLE")
    _, speed_state = speed_status(final_output.linear_speed_m_min, linear_speed)
    power_ratio, power_state = capacity_status(final_output.axis_power_kw,
                                               conveyor.required_axis_power_kw)
    torque_ratio, torque_state = capacity_status(final_output.axis_torque_nm,
                                                 conveyor.required_axis_torque_nm)
    rows = [
        ("Speed", f"{fmt(linear_speed,1)} m/min",
         f"{fmt(final_output.linear_speed_m_min,1)} m/min", speed_state),
        ("Power", f"{fmt(conveyor.required_axis_power_kw,2)} kW",
         f"{fmt(final_output.axis_power_kw,2)} kW", power_state),
        ("Torque", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m",
         f"{fmt(final_output.axis_torque_nm,1)} N·m", torque_state),
    ]
    if supply_mode == "IBR Q catalogue" and ibr_row is not None:
        # Catalog duty screening is distinct from the force/torque design margin.
        rows.append(("IBR service factor (motor-rated)",
                     f"{fmt(ibr_required_fs,2)} minimum",
                     f"{fmt(ibr_perf.service_factor_motor,2)}",
                     "OK" if ibr_perf.service_factor_motor >= ibr_required_fs else "REVIEW"))
        if not (ibr_perf.within_catalogue_motor_limit
                and ibr_perf.within_nominal_input_limit
                and ibr_perf.within_nominal_torque_limit):
            rows.append(("Catalog input/output limits", "Within limits", "Exceeded", "FAIL"))
    if coupling_mode == "Secondary chain transmission":
        # Actual radial loading depends on tight/slack tensions and geometry.
        # Ft alone cannot prove radial compliance.
        rows.append(("Radial load", "Not determined",
                     f"{fmt(drive.admissible_radial_force_n,0)} N", "REVIEW"))

    html = ['<div class="cell-grid" style="grid-template-columns:1.1fr .95fr .95fr .62fr">']
    for label in ("Parameter", "Required", "Available", "Status"):
        html.append(f'<div class="cell"><div class="cell-label">{escape(label)}</div>'
                    f'<div class="cell-value">{escape(label) if label == "Parameter" else "—"}</div></div>')
    for label, req_value, avail_value, status in rows:
        for caption, value in (("Parameter", escape(label)),
                               ("Required", escape(req_value)),
                               ("Available", escape(avail_value)),
                               ("Status", status_badge(status))):
            html.append(f'<div class="cell"><div class="cell-label">{caption}</div>'
                        f'<div class="cell-value">{value}</div></div>')
    st.markdown("".join(html) + "</div>", unsafe_allow_html=True)

    cell_grid([
        ("Available shaft speed", f"{fmt(final_output.axis_speed_rpm,1)} rpm"),
        ("Available shaft torque", f"{fmt(final_output.axis_torque_nm,1)} N·m"),
        ("Available shaft power", f"{fmt(final_output.axis_power_kw,2)} kW"),
        ("Available linear speed", f"{fmt(final_output.linear_speed_m_min,1)} m/min"),
    ], columns=2)
    if coupling_mode == "Secondary chain transmission":
        cell_grid([
            ("Tangential force Ft (not FR)",
             f"{fmt(final_output.radial_tangential_force_n or 0.,0)} N"),
            ("Admissible radial load", f"{fmt(drive.admissible_radial_force_n,0)} N"),
            ("Theoretical Ft-only Dp1",
             f"{fmt(final_output.critical_pitch_diameter_mm,1)} mm"
             if final_output.critical_pitch_diameter_mm is not None else "N/A"),
        ], columns=1)
        st.caption("Radial load remains REVIEW: Ft = T1 − T2 is not the vector sum of chain branch tensions.")

# -----------------------------------------------------------------------------
# AUXILIARY MASS CALCULATOR + GLOSSARY — preserved as collapsed sections.
# -----------------------------------------------------------------------------
with st.expander("Auxiliary carried-mass calculator"):
    density = st.number_input("Material density ρ [kg/m³]", min_value=.01,
                              value=600., step=10., key="density")
    c1, c2 = st.columns(2)
    with c1:
        section_bar("RECTANGULAR PRISM")
        if IMG_PRISM:
            st.image(str(IMG_PRISM), use_container_width=True)
        rr = st.columns(3)
        with rr[0]:
            l1 = st.number_input("ℓ1 [m]", value=3., step=.1, key="p_l1")
        with rr[1]:
            l2 = st.number_input("ℓ2 [m]", value=.4, step=.01, key="p_l2")
        with rr[2]:
            l3 = st.number_input("ℓ3 [m]", value=.2, step=.01, key="p_l3")
        vol, mass = rectangular_mass(l2, l3, l1, density)
        cell_grid([("Volume", f"{fmt(vol,3)} m³"),
                   ("Mass", f"{fmt(mass,1)} kg")], columns=2)
    with c2:
        section_bar("CYLINDER / LOG")
        if IMG_CYLINDER:
            st.image(str(IMG_CYLINDER), use_container_width=True)
        rr = st.columns(2)
        with rr[0]:
            d = st.number_input("Ø [m]", value=.4, step=.01, key="c_d")
        with rr[1]:
            l = st.number_input("ℓ1 [m]", value=3., step=.1, key="c_l")
        vol, mass = cylindrical_mass(d, l, density)
        cell_grid([("Volume", f"{fmt(vol,3)} m³"),
                   ("Mass", f"{fmt(mass,1)} kg")], columns=2)

with st.expander("Engineering notes / variable glossary"):
    glossary = pd.DataFrame([
        ["C", "Conveyor center distance", "m"],
        ["Dp", "Conveyor sprocket pitch diameter", "mm"],
        ["q", "Linear mass of one complete chain strand", "kg/m"],
        ["N", "Number of parallel conveyor chain strands", "—"],
        ["m_load", "Carried material mass", "kg"],
        ["m_top", "Mass of the chain strands in the upper straight span", "kg"],
        ["m_ret", "Mass of the chain strands in the return span", "kg"],
        ["m_arc", "Chain mass on both sprocket half-wraps", "kg"],
        ["F_add", "Additional process force", "N"],
        ["F_top", "Top friction force", "N"],
        ["F_ret", "Guided return friction force", "N"],
        ["s", "Sag in free return", "mm"],
        ["μ_top", "Top friction coefficient", "—"],
        ["μ_ret", "Return friction coefficient", "—"],
        ["f_d", "Drive design factor", "—"],
        ["f_B", "Catalog manufacturer service factor", "—"],
        ["Dp1", "Reducer sprocket pitch diameter", "mm"],
        ["Dp2", "Conveyor-shaft sprocket pitch diameter", "mm"],
        ["α", "Conveyor inclination", "°"],
        ["T1, T2", "Tight- and slack-side transmission chain tension", "N"],
        ["F_R", "Resultant radial force at reducer sprocket", "N"],
    ], columns=["Variable", "Description", "Unit"])
    st.dataframe(glossary, hide_index=True, use_container_width=True)
    st.markdown("""<div class="panel-note">
      <b>Parallel chains:</b> force per strand assumes reasonably equal load sharing;
      chain lengths, sprockets, guiding and tensioning must be compatible.<br>
      <b>Structural integrity:</b> chain ultimate strength, bearing loads, tooth engagement
      and reducer radial loading need additional checks; no structural pass is claimed.
    </div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FULL EQUATION TRACE — LAST SECTION OF THE APP, COLLAPSED BY DEFAULT.
# -----------------------------------------------------------------------------
with st.expander("Calculation methodology · step-by-step equations and current results"):
    st.markdown("""
    This sequence uses the **currently selected inputs**, follows the calculation
    functions in `src/calculations.py`, and explicitly identifies approximations.
    It documents a **quasi-static force model plus uniform linear acceleration**;
    sprocket inertia, shock transients, chain articulation losses and structural
    chain strength are not yet modeled.
    """)
    st.markdown("**1. Geometry and chain mass**")
    st.latex(r"m_{\mathrm{top}}=NqC\qquad m_{\mathrm{ret}}=NqL_{\mathrm{ret}}")
    if internal_return_type == "Guiado":
        st.latex(r"L_{\mathrm{ret}}=C\quad\mathrm{(guided\ return)}")
    else:
        st.latex(r"L_{\mathrm{ret}}\approx C+\frac{8s^2}{3C}\quad\mathrm{(parabolic\ approximation)}")
    st.latex(r"m_{\mathrm{arc}}=Nq\pi D_p\qquad m_{\mathrm{chains}}=m_{\mathrm{top}}+m_{\mathrm{ret}}+m_{\mathrm{arc}}")
    st.caption(f"C={fmt(center_distance_m,5)} m; N={int(strands)}; q={fmt(chain_mass_per_m,2)} kg/m; "
               f"L_ret={fmt(conveyor.return_length_m,4)} m; "
               f"top={fmt(conveyor.top_chain_mass_kg,2)} kg; return={fmt(conveyor.return_chain_mass_kg,2)} kg; "
               f"wraps={fmt(conveyor.arc_chain_mass_kg,2)} kg; TOTAL={fmt(conveyor.total_chain_mass_kg,2)} kg.")
    st.markdown("For guided return, equal upper/lower straight lengths make their chain masses equal. "
                "The wrap mass is counted separately; it is not part of either straight span.")
    st.markdown("**2. Mass supported on the upper track and friction forces**")
    st.latex(r"m_{\mathrm{supported,top}}=m_{\mathrm{load}}+m_{\mathrm{top}}")
    st.latex(r"F_{\mathrm{top}}=\mu_{\mathrm{top}}(m_{\mathrm{load}}+m_{\mathrm{top}})g\cos\alpha")
    if internal_return_type == "Guiado":
        st.latex(r"F_{\mathrm{ret}}=\mu_{\mathrm{ret}}m_{\mathrm{ret}}g\cos\alpha")
    else:
        st.latex(r"F_{\mathrm{ret}}=0\quad\mathrm{(no\ guided\ sliding\ friction\ modeled)}")
        st.markdown("The free hanging return still has tension due to its own weight; "
                    "zero return sliding friction does **not** mean zero chain tension.")
        st.latex(r"w=qg,\quad H\approx\frac{wC^2}{8s},\quad V\approx\frac{wC}{2},\quad T=\sqrt{H^2+V^2}")
        st.caption(f"Catenary approximation per strand: H={fmt(conveyor.catenary_horizontal_n or 0.,1)} N; "
                   f"V={fmt(conveyor.catenary_vertical_n or 0.,1)} N; "
                   f"T={fmt(conveyor.catenary_tension_n or 0.,1)} N.")
    st.caption(f"m_supported,top={fmt(conveyor.top_supported_mass_kg,2)} kg; μ_top={fmt(mu_top,2)}; "
               f"μ_ret={fmt(mu_return,2)}; F_top={fmt(conveyor.top_friction_n,2)} N; "
               f"F_ret={fmt(conveyor.return_friction_n,2)} N.")
    st.markdown("**3. Inclination and steady resistance**")
    st.latex(r"F_{\mathrm{slope}}=m_{\mathrm{load}}g\sin\alpha")
    st.latex(r"F_{\mathrm{steady}}=F_{\mathrm{top}}+F_{\mathrm{ret}}+F_{\mathrm{slope}}+F_{\mathrm{add}}")
    st.caption(f"F_slope={fmt(conveyor.inclination_force_n,2)} N; F_add={fmt(additional_force,2)} N; "
               f"F_steady={fmt(conveyor.regime_force_n,2)} N.")
    st.markdown("**4. Acceleration and moving mass**")
    st.latex(r"v=\frac{v_{\mathrm{min}}}{60},\qquad m_{\mathrm{moving}}=m_{\mathrm{load}}+m_{\mathrm{chains}}")
    st.latex(r"a=\frac{v}{t_a}\ \mathrm{(if\ enabled)},\qquad F_a=m_{\mathrm{moving}}a")
    st.caption(f"v={fmt(linear_speed/60.,4)} m/s; moving mass={fmt(conveyor.moving_mass_kg,2)} kg; "
               f"a={fmt(conveyor.acceleration_m_s2,4)} m/s²; "
               f"F_a={fmt(conveyor.acceleration_force_n,2)} N.")
    st.markdown("**5. Design factor (applied exactly once)**")
    st.latex(r"F_{\mathrm{base}}=F_{\mathrm{steady}}+F_a,\quad F_{\mathrm{design}}=f_d F_{\mathrm{base}}")
    st.latex(r"F_{\mathrm{per\ strand}}=\frac{F_{\mathrm{design}}}{N}")
    st.caption(f"F_base={fmt(conveyor.force_before_design_factor_n,2)} N; "
               f"f_d={fmt(design_factor,2)}; "
               f"F_design={fmt(conveyor.design_force_n,2)} N; "
               f"per strand={fmt(conveyor.force_per_strand_n,2)} N.")
    st.markdown("**6. Conveyor shaft speed, torque and power**")
    st.latex(r"n_{\mathrm{shaft}}=\frac{v_{\mathrm{min}}}{\pi D_p},\quad "
             r"M_{\mathrm{shaft}}=F_{\mathrm{design}}\frac{D_p}{2}")
    st.latex(r"P_{\mathrm{shaft}}=\frac{F_{\mathrm{design}}v}{1000},\quad "
             r"P_{\mathrm{cv}}=\frac{P_{\mathrm{kW}}}{0.73549875}")
    st.caption(f"n={fmt(conveyor.required_axis_speed_rpm,2)} rpm; "
               f"M={fmt(conveyor.required_axis_torque_nm,2)} N·m; "
               f"P={fmt(conveyor.required_axis_power_kw,3)} kW = "
               f"{fmt(conveyor.required_axis_power_cv,3)} cv.")
    st.markdown("**7. Reducer output requirement**")
    if internal_coupling == "Direto":
        st.latex(r"n_{\mathrm{red,req}}=n_{\mathrm{shaft}},\quad "
                 r"M_{\mathrm{red,req}}=M_{\mathrm{shaft}},\quad "
                 r"P_{\mathrm{red,req}}=P_{\mathrm{shaft}}")
    else:
        st.latex(r"i_{\mathrm{sec}}=\frac{D_{p2}}{D_{p1}},\quad\eta_{\mathrm{sec}}\in(0,1]")
        st.latex(r"n_{\mathrm{red,req}}=i_{\mathrm{sec}}n_{\mathrm{shaft}},\quad "
                 r"M_{\mathrm{red,req}}=\frac{M_{\mathrm{shaft}}}{i_{\mathrm{sec}}\eta_{\mathrm{sec}}},\quad "
                 r"P_{\mathrm{red,req}}=\frac{P_{\mathrm{shaft}}}{\eta_{\mathrm{sec}}}")
    st.caption(f"Secondary ratio={fmt(requirement.ratio,4)}; "
               f"required reducer: n={fmt(requirement.required_reducer_speed_rpm,2)} rpm; "
               f"M={fmt(requirement.required_reducer_torque_nm,2)} N·m; "
               f"P={fmt(requirement.required_reducer_power_kw,3)} kW.")
    st.markdown("**8. Available drive: assumptions**")
    if supply_mode == "IBR Q catalogue":
        st.latex(r"i=\frac{n_1}{n_2},\qquad M_{2M}=\frac{7022\,P_{mot,cv}\,\eta}{n_2}")
        st.latex(r"f_{s,cat}=\frac{M_{2Nom}}{M_{2M}},\qquad "
                 r"P_{out,kW}=\frac{2\pi n_2M_{2M}}{60\,000}")
        st.caption(f"IBR Q {ibr_row.size}; i={fmt(ibr_row.ratio,0)}; n1={fmt(ibr_motor_rpm,1)} rpm; "
                   f"n2={fmt(ibr_perf.output_rpm,2)} rpm; motor={fmt(ibr_perf.motor_power_cv,3)} cv; "
                   f"η={fmt(ibr_row.efficiency_pct,0)}%; "
                   f"M2M={fmt(ibr_perf.output_torque_nm,2)} N·m; "
                   f"M2Nom={fmt(ibr_row.nominal_torque_nm,1)} N·m; "
                   f"fs at motor rating={fmt(ibr_perf.service_factor_motor,3)}; "
                   f"fs by selected duty={fmt(ibr_required_fs,2)}; "
                   f"M2Nom/Mbase={fmt(ibr_effective_fs_base,2)}; "
                   f"M2Nom/Mdesign={fmt(ibr_effective_fs_design,2)}.")
        st.latex(r"f_{s,load}=\frac{M_{2Nom}}{M_{red,base}},\quad "
                 r"f_{s,design}=\frac{M_{2Nom}}{M_{red,req}},\quad "
                 r"M_{red,base}=\frac{M_{red,req}}{f_d}")
        st.markdown("These two diagnostic factors describe actual calculated loading and design demand, "
                    "not the IBR catalog factor defined at full motor-rated output. "
                    "Do not compare different definitions without stating which one applies.")
        st.markdown("Printed IBR p.4 defines fs = M2Nom/M2M; its p.9 equation "
                    "is reversed and conflicts with its table. Use the p.4 definition. "
                    "The entered motor may deliver less than catalog PMot; calculate "
                    "the service factor from the entered motor, not blindly from the tabulated PMot. "
                    "The catalog fs criterion and the application's design factor are presented separately.")
        st.markdown("Catalogue: IBR Q frames 075–150, ratios 30/40/50, "
                    "user-provided PDF, printed pp.4–5 and 13–14.")
    elif supply_mode == "Complete gearmotor":
        st.latex(r"P_{\mathrm{red,avail}}=\frac{2\pi n_{\mathrm{out}}M_{\mathrm{out}}}{60\,000}")
        st.caption(f"Catalog output n={fmt(gm_output_speed,2)} rpm, "
                   f"M={fmt(gm_output_torque,2)} N·m ⇒ P={fmt(drive.reducer_output_power_kw,3)} kW. "
                   f"Motor rating={fmt(gm_motor_power,3)} kW = {fmt(kw_to_cv(gm_motor_power),3)} cv.")
        st.markdown("The current available-power calculation uses **catalog output torque and output speed**. "
                    "The motor's entered rated power, ratio and manufacturer service factor are reference inputs, "
                    "not extra power or torque multipliers. Check catalog consistency independently.")
    else:
        st.latex(r"n_m=n_{m,nom}\frac{f_{op}}{f_{nom}},\quad "
                 r"P_{m,model}=P_{m,nom}\min\left(\frac{f_{op}}{f_{nom}},1\right)")
        st.latex(r"P_{m,lim}=\min(P_{m,model},P_{red,input,max})")
        st.latex(r"n_{red}=\frac{n_m}{i_{red}},\quad "
                 r"M_{red}=\min\left(\frac{9550P_{m,lim}}{n_m}i_{red}\eta_{red},M_{red,max}\right)")
        st.markdown("The above corresponds to the existing simplified VFD model "
                    "(constant torque below rated frequency, constant power above). "
                    "It is **not** a validated motor capability curve. "
                    "The motor efficiency input is currently reference-only because rated motor power "
                    "is treated as mechanical shaft power.")
        st.caption(f"Motor rating={fmt(motor_power,3)} kW = {fmt(kw_to_cv(motor_power),3)} cv; "
                   f"reducer available: n={fmt(drive.reducer_output_speed_rpm,2)} rpm; "
                   f"M={fmt(drive.reducer_output_torque_nm,2)} N·m; "
                   f"P={fmt(drive.reducer_output_power_kw,3)} kW.")
    st.markdown("**9. Required versus available at the conveyor shaft**")
    st.latex(r"\lambda_M=\frac{M_{\mathrm{avail}}}{M_{\mathrm{design}}},\quad "
             r"\lambda_P=\frac{P_{\mathrm{avail}}}{P_{\mathrm{design}}},\quad "
             r"\delta_v=\frac{v_{\mathrm{avail}}-v_{\mathrm{desired}}}{v_{\mathrm{desired}}}")
    st.caption(f"Torque ratio λM={fmt(torque_ratio,3)} ({torque_state}); "
               f"power ratio λP={fmt(power_ratio,3)} ({power_state}); "
               f"speed deviation={fmt(100*(final_output.linear_speed_m_min-linear_speed)/linear_speed,2)}% ({speed_state}).")
    st.markdown("Current display rule: capacity ratio ≥ 1.20 ⇒ OK; "
                "1.00–1.20 ⇒ WARNING; below 1.00 ⇒ FAIL. "
                "Speed within ±5% ⇒ OK, otherwise REVIEW. These are interface screening "
                "thresholds, not standards-based equipment certification.")
    st.markdown("**10. Distinct safety/service factors**")
    st.latex(r"f_d=\frac{F_{\mathrm{design}}}{F_{\mathrm{base}}}\quad "
             r"\mathrm{(application\ design\ margin)}")
    st.latex(r"f_B=\frac{M_{a,max}}{M_a}\quad\mathrm{(SEW\ catalog\ definition;\ manufacturer\ specific)}")
    st.latex(r"SF_{\mathrm{chain}}=\frac{F_{\mathrm{breaking}}}{F_{\mathrm{working}}}\quad\mathrm{(not\ calculated)}")
    if supply_mode == "Complete gearmotor":
        st.caption(f"Entered manufacturer catalog service factor: {fmt(gm_service_factor,2)} (reference only).")
    elif supply_mode == "IBR Q catalogue":
        st.latex(r"f_{s,IBR}=\frac{M_{2Nom}}{M_{2M}}")
        st.caption(f"IBR fs at chosen motor={fmt(ibr_perf.service_factor_motor,2)}; "
                   f"IBR minimum by selected service regime={fmt(ibr_required_fs,2)}. "
                   "The meaning of f_d and fs is distinct; verify whether the margins are being combined conservatively.")
    st.markdown("The catalog factor is **not multiplied a second time** by the application design factor. "
                "Actual manufacturer approval depends on duty classification, starts per hour, "
                "temperature, peak loads and catalog conditions. Chain breaking strength is not entered, "
                "so structural chain safety cannot be checked.")
    st.markdown("**11. Secondary transmission radial load: pending model**")
    if internal_coupling == "Direto":
        st.markdown("No secondary chain is selected; this app does not assess loads due to a direct coupling.")
    else:
        st.latex(r"F_t=T_1-T_2=\frac{2M_{red}}{D_{p1}}")
        st.latex(r"\vec F_R=T_1\hat{u}_1+T_2\hat{u}_2,\quad F_R=\lVert\vec F_R\rVert")
        st.caption(f"Current Ft-only estimate={fmt(final_output.radial_tangential_force_n or 0.,2)} N; "
                   f"manufacturer radial limit={fmt(drive.admissible_radial_force_n,2)} N.")
        st.warning("Actual radial load is NOT yet calculated. It requires the secondary center distance, "
                   "branch geometry, tight/slack tensions and operating pretension assumptions. "
                   "Theoretical Ft-only Dp1 is not a recommended diameter and cannot grant OK status.")
        if supply_mode == "IBR Q catalogue":
            st.latex(r"F_{R,IBR}=\frac{2000\,M_{2M}\,f_k\,p}{D_{p1,mm}}")
            st.caption(f"IBR secondary chain f_k=1.25; p={fmt(ibr_p,1)}; "
                       f"FR estimate at entered motor={fmt(ibr_radial_catalogue,1)} N; "
                       f"FR2 limit={fmt(ibr_row.admissible_radial_output_n,1)} N.")
            st.markdown("This IBR formula is a manufacturer selection approximation, "
                        "not the resolved chain-branch tension vector. Its radial-force comparison "
                        "is conditional on the actual load application point and bearing arrangement.")
    st.markdown("**References:** [SEW service factor definition]"
                "(https://download.sew-eurodrive.com/download/html/33346739/en-EN/38925667595.html) · "
                "[SEW application service factor]"
                "(https://download.sew-eurodrive.com/download/html/33346739/en-EN/4007542375551665968267.html)")
