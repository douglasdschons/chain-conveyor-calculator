from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from src.calculations import (
    CompleteGearmotorInput,
    ConveyorInput,
    SecondaryTransmissionInput,
    SeparateDriveInput,
    calculate_conveyor,
    calculate_final_output,
    calculate_secondary_requirement,
    complete_gearmotor_output,
    cylindrical_mass,
    rectangular_mass,
    separate_drive_output,
)

st.set_page_config(
    page_title="Chain Conveyor Calculator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


# =============================================================================
# ASSETS
# =============================================================================

def find_asset(stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        path = ASSETS_DIR / f"{stem}{ext}"
        if path.exists():
            return path

    if ASSETS_DIR.exists():
        target = stem.lower()
        for path in ASSETS_DIR.iterdir():
            if (
                path.is_file()
                and path.stem.lower() == target
                and path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            ):
                return path
    return None


IMG_RETURN = find_asset("return")
IMG_SAG = find_asset("sag")
IMG_DIRECT = find_asset("direct")
IMG_REDUCTION = find_asset("reduction")
IMG_PRISM = find_asset("auxiliary prism")
IMG_CYLINDER = find_asset("auxiliary cylinder")


def image_data_uri(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None

    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/png")

    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


# =============================================================================
# STYLE — COMPACT / EXCEL-LIKE
# =============================================================================

st.markdown(
    """
    <style>
    :root {
        --border: #d9dde4;
        --header: #eaf2f8;
        --header2: #f3f6f9;
        --text: #1f2937;
        --muted: #667085;
        --input: #f4f6f8;
        --blue: #175cd3;
        --ok-bg: #ecfdf3;
        --ok-fg: #067647;
        --warn-bg: #fff7ed;
        --warn-fg: #b54708;
        --bad-bg: #fef3f2;
        --bad-fg: #b42318;
    }

    .block-container {
        max-width: 1760px;
        padding: 0.55rem 0.80rem 1.0rem 0.80rem;
    }

    header[data-testid="stHeader"] {
        height: 2.0rem;
    }

    h1 {
        font-size: 1.22rem !important;
        line-height: 1.15 !important;
        margin: 0 0 0.10rem 0 !important;
        font-weight: 700 !important;
    }

    .app-note {
        font-size: 0.76rem;
        color: var(--muted);
        margin-bottom: 0.38rem;
    }

    .section-bar {
        background: var(--header);
        border: 1px solid var(--border);
        border-bottom: none;
        padding: 0.28rem 0.46rem;
        font-size: 0.82rem;
        line-height: 1.05rem;
        font-weight: 700;
        color: var(--text);
        border-radius: 5px 5px 0 0;
        margin-top: 0.08rem;
    }

    .panel-note {
        border: 1px solid var(--border);
        background: #fff;
        padding: 0.32rem 0.45rem;
        font-size: 0.72rem;
        color: var(--muted);
        line-height: 1.15rem;
        margin-bottom: 0.25rem;
    }

    .cell-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        border-left: 1px solid var(--border);
        border-top: 1px solid var(--border);
        margin-bottom: 0.30rem;
    }

    .cell {
        border-right: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        padding: 0.28rem 0.40rem;
        min-height: 43px;
        background: #fff;
    }

    .cell-label {
        font-size: 0.68rem;
        color: var(--muted);
        line-height: 0.9rem;
    }

    .cell-value {
        font-size: 0.84rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1.05rem;
        margin-top: 0.06rem;
        white-space: nowrap;
    }

    .status-ok, .status-warn, .status-bad {
        display: inline-block;
        border-radius: 4px;
        padding: 0.08rem 0.28rem;
        font-size: 0.66rem;
        font-weight: 700;
    }

    .status-ok { background: var(--ok-bg); color: var(--ok-fg); }
    .status-warn { background: var(--warn-bg); color: var(--warn-fg); }
    .status-bad { background: var(--bad-bg); color: var(--bad-fg); }

    .schematic {
        position: relative;
        width: 100%;
        border: 1px solid var(--border);
        background: #fff;
        overflow: hidden;
    }

    .schematic img {
        display: block;
        width: 100%;
        height: auto;
    }

    .overlay {
        position: absolute;
        transform: translate(-50%, -50%);
        background: rgba(23,92,211,0.94);
        color: white;
        border-radius: 4px;
        padding: 0.08rem 0.22rem;
        font-size: clamp(7px, 0.54vw, 10px);
        font-weight: 700;
        white-space: nowrap;
        box-shadow: 0 1px 3px rgba(16,24,40,.15);
    }

    .tiny-caption {
        font-size: 0.66rem;
        color: var(--muted);
        margin-top: 0.14rem;
        line-height: 0.85rem;
    }

    /* Streamlit widgets */
    div[data-testid="stVerticalBlock"] {
        gap: 0.22rem;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 0.42rem;
    }

    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stToggle"] label {
        font-size: 0.72rem !important;
        line-height: 0.90rem !important;
        margin-bottom: 0.05rem !important;
        color: var(--text) !important;
    }

    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        font-size: 0.75rem !important;
        min-height: 1.85rem !important;
        height: 1.85rem !important;
        padding-top: 0.16rem !important;
        padding-bottom: 0.16rem !important;
        background: var(--input) !important;
    }

    div[data-testid="stSelectbox"] > div > div {
        min-height: 1.85rem !important;
        font-size: 0.75rem !important;
        background: var(--input) !important;
    }

    div[data-testid="stRadio"] {
        margin-top: -0.10rem;
        margin-bottom: -0.10rem;
    }

    div[data-testid="stRadio"] label {
        font-size: 0.71rem !important;
    }

    div[data-testid="stToggle"] {
        margin-top: 0.10rem;
    }

    div[data-testid="stExpander"] summary {
        font-size: 0.74rem !important;
        font-weight: 600 !important;
    }

    div[data-testid="stDataFrame"] {
        font-size: 0.72rem;
    }

    hr {
        margin: 0.38rem 0;
    }

    @media (max-width: 900px) {
        .block-container {
            padding: 0.45rem 0.55rem 1rem 0.55rem;
        }

        .section-bar {
            margin-top: 0.25rem;
        }

        .cell-value {
            white-space: normal;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# SMALL HTML COMPONENTS
# =============================================================================

def fmt(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}"


def section_bar(title: str) -> None:
    st.markdown(f'<div class="section-bar">{title}</div>', unsafe_allow_html=True)


def cell_grid(items: list[tuple[str, str]], columns: int = 2) -> None:
    css_cols = " ".join(["1fr"] * columns)
    html = [f'<div class="cell-grid" style="grid-template-columns:{css_cols};">']
    for label, value in items:
        html.append(
            f'<div class="cell"><div class="cell-label">{label}</div>'
            f'<div class="cell-value">{value}</div></div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def status_badge(status: str) -> str:
    css = {
        "OK": "status-ok",
        "WARNING": "status-warn",
        "REVIEW": "status-warn",
        "FAIL": "status-bad",
    }.get(status, "status-warn")
    return f'<span class="{css}">{status}</span>'


def capacity_status(available: float, required: float) -> tuple[float, str]:
    ratio = available / required if required > 0 else 0.0
    if ratio >= 1.20:
        return ratio, "OK"
    if ratio >= 1.00:
        return ratio, "WARNING"
    return ratio, "FAIL"


def speed_status(available: float, required: float) -> tuple[float, str]:
    error = (available - required) / required if required > 0 else 0.0
    return error, "OK" if abs(error) <= 0.05 else "REVIEW"


# =============================================================================
# SCHEMATICS
# =============================================================================

def render_return_schematic(
    image: Path | None,
    center_distance_m: float,
    pitch_diameter_mm: float,
    f_add_n: float,
    f_top_n: float,
    f_ret_n: float,
    sag_mm: float,
    return_mode: str,
) -> None:
    uri = image_data_uri(image)
    if uri is None:
        st.warning("Return schematic image not found in assets/.")
        return

    overlays = [
        (f"C={fmt(center_distance_m,3)} m", 50.0, 86.0),
        (f"Dp={fmt(pitch_diameter_mm,0)} mm", 88.0, 29.0),
        (f"F_add={fmt(f_add_n,0)} N", 66.0, 20.0),
        (f"F_top={fmt(f_top_n,0)} N", 66.0, 34.0),
    ]

    if return_mode == "Guided return":
        overlays.append((f"F_ret={fmt(f_ret_n,0)} N", 65.0, 69.0))
    else:
        overlays.append((f"s={fmt(sag_mm,0)} mm", 50.0, 68.0))

    labels = "".join(
        f'<span class="overlay" style="left:{x}%;top:{y}%;">{txt}</span>'
        for txt, x, y in overlays
    )

    st.markdown(
        f'<div class="schematic"><img src="{uri}">{labels}</div>',
        unsafe_allow_html=True,
    )


def render_drive_schematic(
    image: Path | None,
    connection_mode: str,
    dp1_mm: float | None,
    dp2_mm: float | None,
    required_speed_rpm: float,
    required_torque_nm: float,
) -> None:
    uri = image_data_uri(image)
    if uri is None:
        st.warning("Drive schematic image not found in assets/.")
        return

    overlays = [
        (f"n_req={fmt(required_speed_rpm,1)} rpm", 51.0, 87.0),
        (f"T_req={fmt(required_torque_nm,1)} N·m", 51.0, 94.0),
    ]

    if connection_mode == "Secondary chain transmission":
        overlays += [
            (f"Dp1={fmt(dp1_mm or 0,0)} mm", 18.0, 77.0),
            (f"Dp2={fmt(dp2_mm or 0,0)} mm", 82.0, 24.0),
        ]

    labels = "".join(
        f'<span class="overlay" style="left:{x}%;top:{y}%;">{txt}</span>'
        for txt, x, y in overlays
    )

    st.markdown(
        f'<div class="schematic"><img src="{uri}">{labels}</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# TITLE
# =============================================================================

st.title("Chain Conveyor Calculator")
st.markdown(
    '<div class="app-note">'
    "System demand · drive selection · required vs available"
    "</div>",
    unsafe_allow_html=True,
)


# =============================================================================
# ROW 1 — SYSTEM / SCHEMATIC / DEMAND
# =============================================================================

col_sys, col_scheme, col_demand = st.columns([1.10, 0.95, 0.82], gap="small")

with col_sys:
    section_bar("1 · SYSTEM INPUTS")

    r = st.columns(3)
    with r[0]:
        center_distance_m = st.number_input(
            "Center distance C [m]", min_value=0.01, value=4.15554, step=0.10
        )
    with r[1]:
        conveyor_dp = st.number_input(
            "Pitch diameter Dp [mm]", min_value=1.0, value=260.0, step=1.0
        )
    with r[2]:
        use_inclination = st.toggle("Inclination", value=False)
        inclination_deg = (
            st.number_input("α [°]", value=0.0, step=1.0)
            if use_inclination else 0.0
        )

    r = st.columns(2)
    with r[0]:
        return_mode = st.selectbox(
            "Return type", ["Guided return", "Sag return"]
        )
    with r[1]:
        if return_mode == "Guided return":
            mu_return = st.number_input(
                "Return friction μ_ret [-]",
                min_value=0.0, value=0.25, step=0.01
            )
            sag_mm = 80.0
            internal_return_type = "Guiado"
        else:
            sag_mm = st.number_input(
                "Return sag s [mm]",
                min_value=1.0, value=80.0, step=5.0
            )
            mu_return = 0.0
            internal_return_type = "Livre"

    r = st.columns(3)
    with r[0]:
        strands = st.number_input(
            "Chain strands [-]", min_value=1, value=4, step=1
        )
    with r[1]:
        chain_mass_per_m = st.number_input(
            "Chain mass [kg/m]", min_value=0.01, value=7.30, step=0.10
        )
    with r[2]:
        mu_top = st.number_input(
            "Top friction μ_top [-]", min_value=0.0, value=0.35, step=0.01
        )

    r = st.columns(3)
    with r[0]:
        load_mass = st.number_input(
            "Carried load [kg]", min_value=0.01, value=276.0, step=10.0
        )
    with r[1]:
        additional_force = st.number_input(
            "Additional F_add [N]", min_value=0.0, value=0.0, step=10.0
        )
    with r[2]:
        linear_speed = st.number_input(
            "Desired speed [m/min]", min_value=0.01, value=32.0, step=1.0
        )

    r = st.columns(3)
    with r[0]:
        consider_acceleration = st.toggle("Acceleration", value=True)
    with r[1]:
        acceleration_time = (
            st.number_input(
                "Acceleration time [s]", min_value=0.01, value=3.0, step=0.5
            )
            if consider_acceleration else 0.0
        )
    with r[2]:
        design_factor = st.number_input(
            "Drive design factor [-]",
            min_value=1.0, value=1.50, step=0.05,
            help=(
                "Margin applied to calculated drive force, torque and power. "
                "It is not the chain breaking-load safety factor."
            ),
        )


conveyor = calculate_conveyor(
    ConveyorInput(
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
    )
)

with col_scheme:
    section_bar("SYSTEM SCHEMATIC")
    render_return_schematic(
        IMG_RETURN if return_mode == "Guided return" else IMG_SAG,
        center_distance_m,
        conveyor_dp,
        additional_force,
        conveyor.top_friction_n,
        conveyor.return_friction_n,
        sag_mm,
        return_mode,
    )
    st.markdown(
        '<div class="tiny-caption">'
        "Live values · illustrative schematic"
        "</div>",
        unsafe_allow_html=True,
    )

with col_demand:
    section_bar("SYSTEM DEMAND")
    cell_grid(
        [
            ("Design force", f"{fmt(conveyor.design_force_n,0)} N"),
            ("Force / strand", f"{fmt(conveyor.force_per_strand_n,0)} N"),
            ("Shaft torque", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m"),
            ("Power", f"{fmt(conveyor.required_axis_power_kw,2)} kW"),
            ("Power", f"{fmt(conveyor.required_axis_power_cv,2)} cv"),
            ("Shaft speed", f"{fmt(conveyor.required_axis_speed_rpm,1)} rpm"),
            ("Total chain mass", f"{fmt(conveyor.total_chain_mass_kg,1)} kg"),
            ("Steady resistance", f"{fmt(conveyor.regime_force_n,0)} N"),
        ],
        columns=2,
    )
    if consider_acceleration:
        cell_grid(
            [
                ("Acceleration", f"{fmt(conveyor.acceleration_m_s2,3)} m/s²"),
                ("Acceleration force", f"{fmt(conveyor.acceleration_force_n,0)} N"),
            ],
            columns=2,
        )


# =============================================================================
# ROW 2 — CONNECTION / PROVIDED DRIVE / COMPARISON
# =============================================================================

col_conn, col_drive, col_compare = st.columns([0.92, 1.20, 0.90], gap="small")

with col_conn:
    section_bar("2 · DRIVE CONNECTION")

    coupling_mode = st.radio(
        "Connection",
        ["Direct", "Secondary chain transmission"],
        horizontal=True,
    )

    if coupling_mode == "Secondary chain transmission":
        internal_coupling = "Transmissão secundária"

        r = st.columns(3)
        with r[0]:
            secondary_dp1 = st.number_input(
                "Dp1 [mm]", min_value=1.0, value=170.0, step=1.0
            )
        with r[1]:
            secondary_dp2 = st.number_input(
                "Dp2 [mm]", min_value=1.0, value=202.66, step=1.0
            )
        with r[2]:
            secondary_eff = st.number_input(
                "η_sec [%]", min_value=1.0, max_value=100.0,
                value=98.0, step=0.5
            )
    else:
        internal_coupling = "Direto"
        secondary_dp1 = 1.0
        secondary_dp2 = 1.0
        secondary_eff = 100.0

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

with col_conn:
    render_drive_schematic(
        IMG_DIRECT if coupling_mode == "Direct" else IMG_REDUCTION,
        coupling_mode,
        secondary_dp1 if coupling_mode != "Direct" else None,
        secondary_dp2 if coupling_mode != "Direct" else None,
        requirement.required_reducer_speed_rpm,
        requirement.required_reducer_torque_nm,
    )

    cell_grid(
        [
            ("Req. reducer speed", f"{fmt(requirement.required_reducer_speed_rpm,1)} rpm"),
            ("Req. reducer torque", f"{fmt(requirement.required_reducer_torque_nm,1)} N·m"),
            ("Req. reducer power", f"{fmt(requirement.required_reducer_power_kw,2)} kW"),
        ],
        columns=1,
    )


with col_drive:
    section_bar("3 · PROVIDED DRIVE")

    supply_mode = st.radio(
        "Supply mode",
        ["Complete gearmotor", "Separate gearbox + motor"],
        horizontal=True,
    )

    if supply_mode == "Complete gearmotor":
        r1 = st.columns(4)
        with r1[0]:
            gm_manufacturer = st.text_input("Manufacturer", "SEW-EURODRIVE")
        with r1[1]:
            gm_model = st.text_input("Model", "")
        with r1[2]:
            gm_motor_power = st.number_input("Motor kW", value=15.0, step=0.5)
        with r1[3]:
            gm_motor_speed = st.number_input("Motor rpm", value=1777.0, step=1.0)

        r2 = st.columns(4)
        with r2[0]:
            gm_ratio = st.number_input("Ratio", value=22.37, step=0.01)
        with r2[1]:
            gm_output_speed = st.number_input("Output rpm", value=79.0, step=1.0)
        with r2[2]:
            gm_output_torque = st.number_input(
                "Output N·m", value=1790.0, step=10.0
            )
        with r2[3]:
            gm_radial = st.number_input(
                "Radial limit [N]", value=15600.0, step=100.0
            )

        gm_service_factor = st.number_input(
            "Manufacturer service factor [-]",
            value=1.50, step=0.05,
            help="Manufacturer-specific factor; not the application design factor.",
        )

        drive = complete_gearmotor_output(
            CompleteGearmotorInput(
                manufacturer=gm_manufacturer,
                model=gm_model,
                motor_power_kw=gm_motor_power,
                motor_speed_rpm=gm_motor_speed,
                output_speed_rpm=gm_output_speed,
                total_ratio=gm_ratio,
                output_torque_nm=gm_output_torque,
                admissible_radial_force_n=gm_radial,
                manufacturer_service_factor=gm_service_factor,
            )
        )

    else:
        r1 = st.columns(4)
        with r1[0]:
            reducer_manufacturer = st.text_input("Gearbox mfr.", "Geremia")
        with r1[1]:
            reducer_model = st.text_input("Gearbox model", "GD30/2R")
        with r1[2]:
            reducer_ratio = st.number_input("Gear ratio", value=35.0, step=0.01)
        with r1[3]:
            reducer_eff = st.number_input("Gear η [%]", value=96.0, step=0.5)

        r2 = st.columns(3)
        with r2[0]:
            reducer_max_torque = st.number_input(
                "Max torque [N·m]", value=370.0, step=10.0
            )
        with r2[1]:
            reducer_radial = st.number_input(
                "Radial limit [N]", value=6300.0, step=100.0
            )
        with r2[2]:
            reducer_max_power = st.number_input(
                "Max input [kW]", value=1.50, step=0.10
            )

        r3 = st.columns(4)
        with r3[0]:
            motor_manufacturer = st.text_input("Motor mfr.", "WEG")
        with r3[1]:
            motor_model = st.text_input("Motor model", "")
        with r3[2]:
            motor_power = st.number_input("Motor kW", value=1.50, step=0.10)
        with r3[3]:
            motor_speed = st.number_input("Motor rpm", value=1745.0, step=1.0)

        r4 = st.columns(3)
        with r4[0]:
            motor_eff = st.number_input("Motor η [%]", value=86.5, step=0.1)
        with r4[1]:
            nominal_freq = st.number_input("Rated Hz", value=60.0, step=1.0)
        with r4[2]:
            operating_freq = st.number_input("Operating Hz", value=60.0, step=1.0)

        drive = separate_drive_output(
            SeparateDriveInput(
                reducer_manufacturer=reducer_manufacturer,
                reducer_model=reducer_model,
                reducer_ratio=reducer_ratio,
                reducer_efficiency_pct=reducer_eff,
                reducer_max_torque_nm=reducer_max_torque,
                reducer_admissible_radial_force_n=reducer_radial,
                reducer_max_input_power_kw=reducer_max_power,
                motor_manufacturer=motor_manufacturer,
                motor_model=motor_model,
                motor_power_kw=motor_power,
                motor_speed_rpm=motor_speed,
                motor_efficiency_pct=motor_eff,
                nominal_frequency_hz=nominal_freq,
                operating_frequency_hz=operating_freq,
            )
        )


final_output = calculate_final_output(
    drive,
    transmission,
    conveyor_dp,
)


with col_compare:
    section_bar("4 · REQUIRED × AVAILABLE")

    speed_dev, speed_state = speed_status(
        final_output.linear_speed_m_min, linear_speed
    )
    power_ratio, power_state = capacity_status(
        final_output.axis_power_kw, conveyor.required_axis_power_kw
    )
    torque_ratio, torque_state = capacity_status(
        final_output.axis_torque_nm, conveyor.required_axis_torque_nm
    )

    compare_html = [
        '<div class="cell-grid" style="grid-template-columns:1.15fr .85fr .85fr .65fr;">',
        '<div class="cell"><div class="cell-label">Parameter</div><div class="cell-value">—</div></div>',
        '<div class="cell"><div class="cell-label">Required</div><div class="cell-value">—</div></div>',
        '<div class="cell"><div class="cell-label">Available</div><div class="cell-value">—</div></div>',
        '<div class="cell"><div class="cell-label">Status</div><div class="cell-value">—</div></div>',
    ]

    rows = [
        (
            "Speed",
            f"{fmt(linear_speed,1)} m/min",
            f"{fmt(final_output.linear_speed_m_min,1)} m/min",
            speed_state,
        ),
        (
            "Power",
            f"{fmt(conveyor.required_axis_power_kw,2)} kW",
            f"{fmt(final_output.axis_power_kw,2)} kW",
            power_state,
        ),
        (
            "Torque",
            f"{fmt(conveyor.required_axis_torque_nm,1)} N·m",
            f"{fmt(final_output.axis_torque_nm,1)} N·m",
            torque_state,
        ),
    ]

    if coupling_mode == "Secondary chain transmission":
        radial_force = final_output.radial_tangential_force_n or 0.0
        radial_ratio = (
            drive.admissible_radial_force_n / radial_force
            if radial_force > 0 else 0.0
        )
        radial_state = "OK" if radial_ratio >= 1.0 else "FAIL"
        rows.append(
            (
                "Radial load",
                f"{fmt(radial_force,0)} N",
                f"{fmt(drive.admissible_radial_force_n,0)} N",
                radial_state,
            )
        )

    for label, required, available, status in rows:
        compare_html += [
            f'<div class="cell"><div class="cell-label">{label}</div><div class="cell-value">{label}</div></div>',
            f'<div class="cell"><div class="cell-label">Required</div><div class="cell-value">{required}</div></div>',
            f'<div class="cell"><div class="cell-label">Available</div><div class="cell-value">{available}</div></div>',
            f'<div class="cell"><div class="cell-label">Status</div><div class="cell-value">{status_badge(status)}</div></div>',
        ]

    compare_html.append("</div>")
    st.markdown("".join(compare_html), unsafe_allow_html=True)

    cell_grid(
        [
            ("Available shaft speed", f"{fmt(final_output.axis_speed_rpm,1)} rpm"),
            ("Available shaft torque", f"{fmt(final_output.axis_torque_nm,1)} N·m"),
            ("Available shaft power", f"{fmt(final_output.axis_power_kw,2)} kW"),
            ("Available linear speed", f"{fmt(final_output.linear_speed_m_min,1)} m/min"),
        ],
        columns=2,
    )

    if coupling_mode == "Secondary chain transmission":
        radial_force = final_output.radial_tangential_force_n or 0.0
        critical = final_output.critical_pitch_diameter_mm
        cell_grid(
            [
                ("Tangential force", f"{fmt(radial_force,0)} N"),
                ("Radial limit", f"{fmt(drive.admissible_radial_force_n,0)} N"),
                (
                    "Critical Dp",
                    f"{fmt(critical,1)} mm" if critical is not None else "N/A",
                ),
            ],
            columns=1,
        )


# =============================================================================
# COLLAPSED AUXILIARY SECTIONS
# =============================================================================

with st.expander("Auxiliary carried-mass calculator"):
    density = st.number_input(
        "Material density [kg/m³]",
        min_value=1.0,
        value=1150.0,
        step=10.0,
        key="density",
    )

    c1, c2 = st.columns(2)

    with c1:
        section_bar("RECTANGULAR PRISM")
        if IMG_PRISM:
            st.image(str(IMG_PRISM), use_container_width=True)

        rr = st.columns(3)
        with rr[0]:
            l1 = st.number_input("ℓ1 [m]", value=3.0, step=0.1, key="p_l1")
        with rr[1]:
            l2 = st.number_input("ℓ2 [m]", value=0.40, step=0.01, key="p_l2")
        with rr[2]:
            l3 = st.number_input("ℓ3 [m]", value=0.20, step=0.01, key="p_l3")

        vol, mass = rectangular_mass(l2, l3, l1, density)
        cell_grid(
            [("Volume", f"{fmt(vol,3)} m³"), ("Mass", f"{fmt(mass,1)} kg")],
            columns=2,
        )

    with c2:
        section_bar("CYLINDER / LOG")
        if IMG_CYLINDER:
            st.image(str(IMG_CYLINDER), use_container_width=True)

        rr = st.columns(2)
        with rr[0]:
            d = st.number_input("Ø [m]", value=0.40, step=0.01, key="c_d")
        with rr[1]:
            l = st.number_input("ℓ1 [m]", value=3.0, step=0.1, key="c_l")

        vol, mass = cylindrical_mass(d, l, density)
        cell_grid(
            [("Volume", f"{fmt(vol,3)} m³"), ("Mass", f"{fmt(mass,1)} kg")],
            columns=2,
        )


with st.expander("Engineering notes / variable glossary"):
    glossary = pd.DataFrame(
        [
            ["C", "Center distance", "m"],
            ["Dp", "Conveyor sprocket pitch diameter", "mm"],
            ["F_add", "Additional process force", "N"],
            ["F_top", "Top friction force", "N"],
            ["F_ret", "Guided return friction force", "N"],
            ["s", "Sag", "mm"],
            ["μ_top", "Top friction coefficient", "-"],
            ["μ_ret", "Return friction coefficient", "-"],
            ["Dp1", "Reducer sprocket pitch diameter", "mm"],
            ["Dp2", "Conveyor-shaft sprocket pitch diameter", "mm"],
            ["α", "Conveyor inclination", "°"],
        ],
        columns=["Variable", "Description", "Unit"],
    )
    st.dataframe(glossary, hide_index=True, use_container_width=True)

    st.markdown(
        '<div class="panel-note">'
        "<b>Drive design factor:</b> margin applied to calculated force, torque and "
        "power demand. It is not the structural chain breaking-load safety factor.<br>"
        "<b>Parallel chains:</b> force per strand assumes compatible chain lengths, "
        "synchronized sprockets, level guides, equivalent tensioning and similar wear."
        "</div>",
        unsafe_allow_html=True,
    )
