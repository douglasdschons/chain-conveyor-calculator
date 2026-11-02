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
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def find_asset(stem: str) -> Path | None:
    """Find an asset by filename without extension."""
    extensions = (".png", ".jpg", ".jpeg", ".webp")

    for ext in extensions:
        candidate = ASSETS_DIR / f"{stem}{ext}"
        if candidate.exists():
            return candidate

    if ASSETS_DIR.exists():
        wanted = stem.lower()
        for candidate in ASSETS_DIR.iterdir():
            if (
                candidate.is_file()
                and candidate.stem.lower() == wanted
                and candidate.suffix.lower() in extensions
            ):
                return candidate

    return None


GUIDED_RETURN_IMAGE = find_asset("return")
SAG_RETURN_IMAGE = find_asset("sag")
DIRECT_IMAGE = find_asset("direct")
REDUCTION_IMAGE = find_asset("reduction")
AUXILIARY_PRISM_IMAGE = find_asset("auxiliary prism")
AUXILIARY_CYLINDER_IMAGE = find_asset("auxiliary cylinder")


st.markdown(
    """
    <style>
        .block-container {
            max-width: 1550px;
            padding-top: 1.35rem;
            padding-bottom: 3rem;
        }
        h1 {margin-bottom: 0.10rem;}
        .app-subtitle {
            color: #667085;
            margin-bottom: 1.25rem;
            font-size: 0.98rem;
        }
        .section-kicker {
            color: #667085;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin-bottom: 0.1rem;
        }
        .section-title {
            color: #101828;
            font-size: 1.20rem;
            font-weight: 700;
            margin: 0 0 0.65rem 0;
        }
        .soft-note {
            background: #F8FAFC;
            border-left: 4px solid #98A2B3;
            padding: 0.72rem 0.90rem;
            border-radius: 5px;
            color: #475467;
            font-size: 0.88rem;
            margin-top: 0.55rem;
        }
        .status-ok {
            color: #067647;
            background: #ECFDF3;
            border: 1px solid #ABEFC6;
            border-radius: 999px;
            padding: 0.18rem 0.52rem;
            font-weight: 700;
            font-size: 0.78rem;
        }
        .status-warn {
            color: #B54708;
            background: #FFFAEB;
            border: 1px solid #FEDF89;
            border-radius: 999px;
            padding: 0.18rem 0.52rem;
            font-weight: 700;
            font-size: 0.78rem;
        }
        .status-bad {
            color: #B42318;
            background: #FEF3F2;
            border: 1px solid #FECDCA;
            border-radius: 999px;
            padding: 0.18rem 0.52rem;
            font-weight: 700;
            font-size: 0.78rem;
        }
        .engineering-card {
            border: 1px solid #E4E7EC;
            border-radius: 10px;
            padding: 0.85rem 0.95rem;
            background: #FFFFFF;
            margin-bottom: 0.65rem;
        }
        .engineering-card .label {
            color: #667085;
            font-size: 0.78rem;
            margin-bottom: 0.08rem;
        }
        .engineering-card .value {
            color: #101828;
            font-size: 1.02rem;
            font-weight: 700;
        }
        .engineering-card .sub {
            color: #667085;
            font-size: 0.77rem;
            margin-top: 0.15rem;
        }
        .result-card {
            border: 1px solid #E4E7EC;
            border-radius: 9px;
            padding: 0.68rem 0.78rem;
            background: #FFFFFF;
            min-height: 82px;
            margin-bottom: 0.55rem;
        }

        .result-card .result-label {
            color: #475467;
            font-size: 0.82rem;
            font-weight: 500;
            line-height: 1.25;
            margin-bottom: 0.20rem;
        }

        .result-card .result-value {
            color: #101828;
            font-size: 1.00rem;
            font-weight: 700;
            line-height: 1.20;
            white-space: nowrap;
        }

        div[data-testid="stMetric"] {
            border: 1px solid #E4E7EC;
            padding: 0.76rem 0.86rem;
            border-radius: 10px;
            background: #FFFFFF;
        }
        div[data-testid="stMetricLabel"] {color: #667085;}
        .schematic-frame {
            position: relative;
            width: 100%;
            aspect-ratio: 16 / 9;
            overflow: hidden;
            border: 1px solid #E4E7EC;
            border-radius: 12px;
            background: #FFFFFF;
        }
        .schematic-frame img {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .diagram-value {
            position: absolute;
            transform: translate(-50%, -50%);
            background: rgba(23, 92, 211, 0.93);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.72);
            border-radius: 6px;
            padding: 0.16rem 0.38rem;
            font-size: clamp(9px, 0.85vw, 14px);
            font-weight: 700;
            line-height: 1.15;
            white-space: nowrap;
            box-shadow: 0 1px 4px rgba(16, 24, 40, 0.16);
        }
        .diagram-caption {
            color: #667085;
            font-size: 0.77rem;
            margin-top: 0.28rem;
        }
        hr {
            margin-top: 1.35rem;
            margin-bottom: 1.35rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}"


def image_to_data_uri(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    mime = mime_map.get(path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def status_for_capacity(ratio: float) -> tuple[str, str]:
    if ratio >= 1.20:
        return "OK", "status-ok"
    if ratio >= 1.00:
        return "WARNING", "status-warn"
    return "FAIL", "status-bad"


def status_for_speed(error: float) -> tuple[str, str]:
    if abs(error) <= 0.05:
        return "OK", "status-ok"
    return "REVIEW", "status-warn"


def capacity_ratio(available: float, required: float) -> float:
    return available / required if required > 0 else 0.0


def render_schematic(
    image_path: Path | None,
    *,
    center_distance_m: float,
    pitch_diameter_mm: float,
    additional_force_n: float,
    top_friction_n: float,
    return_friction_n: float,
    sag_mm: float,
    return_mode: str,
) -> None:
    """Overlay live calculated values on the static conveyor schematic."""
    image_uri = image_to_data_uri(image_path)

    if image_uri is None:
        expected = "return.*" if return_mode == "Guided return" else "sag.*"
        st.warning(f"Image not found: `{expected}` inside `assets/`.")
        return

    # Coordinates are percentages of the 16:9 source image.
    # They can be adjusted later if the final English images move the labels.
    overlays = [
        (f"C = {fmt(center_distance_m, 3)} m", 50.0, 85.5),
        (f"Dp = {fmt(pitch_diameter_mm, 0)} mm", 91.0, 28.0),
        (f"F_add = {fmt(additional_force_n, 0)} N", 65.0, 21.5),
        (f"F_top = {fmt(top_friction_n, 0)} N", 65.0, 34.5),
    ]

    if return_mode == "Guided return":
        overlays.append(
            (f"F_ret = {fmt(return_friction_n, 0)} N", 64.5, 72.5)
        )
    else:
        overlays.append(
            (f"s = {fmt(sag_mm, 0)} mm", 50.0, 69.0)
        )

    overlay_html = "".join(
        f'<span class="diagram-value" style="left:{left:.2f}%; top:{top:.2f}%;">{text}</span>'
        for text, left, top in overlays
    )

    st.markdown(
        f"""
        <div class="schematic-frame">
            <img src="{image_uri}" alt="Chain conveyor schematic">
            {overlay_html}
        </div>
        <div class="diagram-caption">
            Live calculation values are superimposed on the schematic. The drawing is illustrative and is not a manufacturing drawing.
        </div>
        """,
        unsafe_allow_html=True,
    )




def render_drive_schematic(
    image_path: Path | None,
    *,
    connection_mode: str,
    dp1_mm: float | None,
    dp2_mm: float | None,
    required_speed_rpm: float,
    required_torque_nm: float,
) -> None:
    """Show direct/reduction image with live engineering values."""
    image_uri = image_to_data_uri(image_path)

    if image_uri is None:
        expected = "direct.*" if connection_mode == "Direct" else "reduction.*"
        st.warning(f"Image not found: `{expected}` inside `assets/`.")
        return

    overlays = [
        (f"n_req = {fmt(required_speed_rpm, 1)} rpm", 50.0, 86.0),
        (f"T_req = {fmt(required_torque_nm, 1)} N·m", 50.0, 94.0),
    ]

    if connection_mode == "Secondary chain transmission":
        if dp1_mm is not None:
            overlays.append((f"Dp1 = {fmt(dp1_mm, 0)} mm", 18.0, 76.0))
        if dp2_mm is not None:
            overlays.append((f"Dp2 = {fmt(dp2_mm, 0)} mm", 82.0, 23.0))

    overlay_html = "".join(
        f'<span class="diagram-value" style="left:{left:.2f}%; top:{top:.2f}%;">{label}</span>'
        for label, left, top in overlays
    )

    st.markdown(
        f"""
        <div class="schematic-frame">
            <img src="{image_uri}" alt="Drive connection schematic">
            {overlay_html}
        </div>
        <div class="diagram-caption">
            Required values are shown on the selected drive arrangement.
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("Chain Conveyor Calculator")
st.markdown(
    '<div class="app-subtitle">'
    "Engineering sizing of the conveyor, drive selection and direct comparison "
    "between system demand and available drive capacity."
    "</div>",
    unsafe_allow_html=True,
)


# STEP 1 ----------------------------------------------------------------------

st.markdown(
    '<div class="section-kicker">Step 1</div>'
    '<div class="section-title">System to be solved</div>',
    unsafe_allow_html=True,
)

system_col, schematic_col = st.columns([1.05, 0.95], gap="large")

with system_col:
    geometry_row = st.columns(3)

    with geometry_row[0]:
        center_distance_m = st.number_input(
            "Center distance C [m]",
            min_value=0.01,
            value=4.15554,
            step=0.10,
            help="Distance between the centers of the conveyor sprockets.",
        )

    with geometry_row[1]:
        conveyor_dp = st.number_input(
            "Pitch diameter Dp [mm]",
            min_value=1.0,
            value=260.0,
            step=1.0,
        )

    with geometry_row[2]:
        use_inclination = st.toggle(
            "Consider conveyor inclination",
            value=False,
            help="Enable this option when the conveyor is not horizontal.",
        )
        if use_inclination:
            inclination_deg = st.number_input(
                "Conveyor inclination α [°]",
                value=0.0,
                step=1.0,
            )
        else:
            inclination_deg = 0.0

    return_row = st.columns(2)

    with return_row[0]:
        return_mode = st.selectbox(
            "Return type",
            ["Guided return", "Sag return"],
        )

    with return_row[1]:
        if return_mode == "Guided return":
            mu_return = st.number_input(
                "Return friction coefficient μ_ret [-]",
                min_value=0.0,
                value=0.25,
                step=0.01,
            )
            sag_mm = 80.0
            internal_return_type = "Guiado"
        else:
            sag_mm = st.number_input(
                "Return sag s [mm]",
                min_value=1.0,
                value=80.0,
                step=5.0,
            )
            mu_return = 0.0
            internal_return_type = "Livre"

    chain_row = st.columns(3)

    with chain_row[0]:
        strands = st.number_input(
            "Number of chain strands [-]",
            min_value=1,
            value=4,
            step=1,
        )

    with chain_row[1]:
        chain_mass_per_m = st.number_input(
            "Chain linear mass [kg/m]",
            min_value=0.01,
            value=7.30,
            step=0.10,
        )

    with chain_row[2]:
        mu_top = st.number_input(
            "Top friction coefficient μ_top [-]",
            min_value=0.0,
            value=0.35,
            step=0.01,
        )

    load_row = st.columns(3)

    with load_row[0]:
        load_mass = st.number_input(
            "Carried load mass [kg]",
            min_value=0.01,
            value=276.0,
            step=10.0,
        )
        st.markdown(
            '<a href="#wood-mass-helper" style="font-size:0.80rem;">'
            'Open auxiliary mass calculator ↓</a>',
            unsafe_allow_html=True,
        )

    with load_row[1]:
        additional_force = st.number_input(
            "Additional force F_add [N]",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )

    with load_row[2]:
        linear_speed = st.number_input(
            "Desired chain speed [m/min]",
            min_value=0.01,
            value=32.0,
            step=1.0,
        )

    design_row = st.columns(3)

    with design_row[0]:
        consider_acceleration = st.toggle(
            "Consider acceleration",
            value=True,
            help="Enable to include the conveyor acceleration force in the drive demand.",
        )

    with design_row[1]:
        if consider_acceleration:
            acceleration_time = st.number_input(
                "Acceleration time [s]",
                min_value=0.01,
                value=3.0,
                step=0.5,
            )
        else:
            acceleration_time = 0.0
            st.caption("Acceleration is not included.")

    with design_row[2]:
        design_factor = st.number_input(
            "Drive design factor [-]",
            min_value=1.0,
            value=1.50,
            step=0.05,
            help=(
                "Margin applied to calculated drive force, torque and power demand. "
                "This is not the chain breaking-load safety factor."
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


with schematic_col:
    st.markdown("#### Conveyor schematic")

    selected_image = (
        GUIDED_RETURN_IMAGE
        if return_mode == "Guided return"
        else SAG_RETURN_IMAGE
    )

    render_schematic(
        selected_image,
        center_distance_m=center_distance_m,
        pitch_diameter_mm=conveyor_dp,
        additional_force_n=additional_force,
        top_friction_n=conveyor.top_friction_n,
        return_friction_n=conveyor.return_friction_n,
        sag_mm=sag_mm,
        return_mode=return_mode,
    )


# STEP 2 ----------------------------------------------------------------------

st.divider()
st.markdown(
    '<div class="section-kicker">Step 2</div>'
    '<div class="section-title">System demand</div>',
    unsafe_allow_html=True,
)

demand_row_1 = st.columns(3)
demand_row_2 = st.columns(3)

demand_cards = [
    (demand_row_1[0], "Design force", f"{fmt(conveyor.design_force_n, 0)} N"),
    (demand_row_1[1], "Force per strand", f"{fmt(conveyor.force_per_strand_n, 0)} N"),
    (demand_row_1[2], "Required shaft torque", f"{fmt(conveyor.required_axis_torque_nm, 1)} N·m"),
    (demand_row_2[0], "Required power", f"{fmt(conveyor.required_axis_power_kw, 2)} kW"),
    (demand_row_2[1], "Required power", f"{fmt(conveyor.required_axis_power_cv, 2)} cv"),
    (demand_row_2[2], "Required shaft speed", f"{fmt(conveyor.required_axis_speed_rpm, 1)} rpm"),
]

for column, label, value in demand_cards:
    column.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">{label}</div>
            <div class="result-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

secondary_items = [
    f"Total chain mass: <b>{fmt(conveyor.total_chain_mass_kg, 1)} kg</b>",
    f"Steady-state resistance: <b>{fmt(conveyor.regime_force_n, 0)} N</b>",
]

if consider_acceleration:
    secondary_items.extend(
        [
            f"Acceleration: <b>{fmt(conveyor.acceleration_m_s2, 3)} m/s²</b>",
            f"Acceleration force: <b>{fmt(conveyor.acceleration_force_n, 0)} N</b>",
        ]
    )

st.markdown(
    '<div class="soft-note">' + " · ".join(secondary_items) + "</div>",
    unsafe_allow_html=True,
)


# STEP 3 ----------------------------------------------------------------------

st.divider()
st.markdown(
    '<div class="section-kicker">Step 3</div>'
    '<div class="section-title">Connection between drive and conveyor shaft</div>',
    unsafe_allow_html=True,
)

connection_input_col, connection_image_col = st.columns([0.88, 1.12], gap="large")

with connection_input_col:
    coupling_mode = st.radio(
        "Drive connection",
        ["Direct", "Secondary chain transmission"],
        horizontal=False,
    )

    if coupling_mode == "Secondary chain transmission":
        internal_coupling_type = "Transmissão secundária"

        secondary_dp1 = st.number_input(
            "Reducer sprocket pitch diameter Dp1 [mm]",
            min_value=1.0,
            value=170.0,
            step=1.0,
        )

        secondary_dp2 = st.number_input(
            "Conveyor-shaft sprocket pitch diameter Dp2 [mm]",
            min_value=1.0,
            value=202.66,
            step=1.0,
        )

        secondary_eff = st.number_input(
            "Secondary transmission efficiency η_sec [%]",
            min_value=1.0,
            max_value=100.0,
            value=98.0,
            step=0.5,
        )

    else:
        internal_coupling_type = "Direto"
        secondary_dp1 = 1.0
        secondary_dp2 = 1.0
        secondary_eff = 100.0


transmission = SecondaryTransmissionInput(
    coupling_type=internal_coupling_type,
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

with connection_input_col:
    st.markdown("**Required at reducer output**")
    req1, req2, req3 = st.columns(3)

    result_card_data = [
        (req1, "Speed", f"{fmt(requirement.required_reducer_speed_rpm, 1)} rpm"),
        (req2, "Torque", f"{fmt(requirement.required_reducer_torque_nm, 1)} N·m"),
        (req3, "Power", f"{fmt(requirement.required_reducer_power_kw, 2)} kW"),
    ]

    for column, label, value in result_card_data:
        column.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">{label}</div>
                <div class="result-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with connection_image_col:
    selected_drive_image = (
        DIRECT_IMAGE if coupling_mode == "Direct" else REDUCTION_IMAGE
    )

    render_drive_schematic(
        selected_drive_image,
        connection_mode=coupling_mode,
        dp1_mm=secondary_dp1 if coupling_mode != "Direct" else None,
        dp2_mm=secondary_dp2 if coupling_mode != "Direct" else None,
        required_speed_rpm=requirement.required_reducer_speed_rpm,
        required_torque_nm=requirement.required_reducer_torque_nm,
    )


# STEP 4 ----------------------------------------------------------------------

st.divider()
st.markdown(
    '<div class="section-kicker">Step 4</div>'
    '<div class="section-title">Provided drive</div>',
    unsafe_allow_html=True,
)

supply_mode = st.radio(
    "How will the drive be specified?",
    ["Complete gearmotor", "Separate gearbox + motor"],
    horizontal=True,
)

drive_input_col, drive_output_col = st.columns([1.20, 0.80], gap="large")

with drive_input_col:
    if supply_mode == "Complete gearmotor":
        st.markdown("#### Complete gearmotor")
        st.caption("Enter the certified output data supplied by the gearmotor manufacturer.")

        gm_a, gm_b = st.columns(2)

        with gm_a:
            gm_manufacturer = st.text_input("Manufacturer", value="SEW-EURODRIVE")
            gm_model = st.text_input("Model / designation", value="")
            gm_motor_power = st.number_input("Motor rated power [kW]", value=15.0, step=0.5)
            gm_motor_speed = st.number_input("Motor rated speed [rpm]", value=1777.0, step=1.0)
            gm_ratio = st.number_input("Total gear ratio [-]", value=22.37, step=0.01)

        with gm_b:
            gm_output_speed = st.number_input("Output speed [rpm]", value=79.0, step=1.0)
            gm_output_torque = st.number_input("Output torque [N·m]", value=1790.0, step=10.0)
            gm_radial = st.number_input("Admissible output radial force [N]", value=15600.0, step=100.0)
            gm_service_factor = st.number_input(
                "Manufacturer service factor [-]",
                value=1.50,
                step=0.05,
                help="Manufacturer-specific factor. Do not replace the application design factor with this value.",
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
        st.markdown("#### Gearbox")
        gb_a, gb_b = st.columns(2)

        with gb_a:
            reducer_manufacturer = st.text_input("Gearbox manufacturer", value="Geremia")
            reducer_model = st.text_input("Gearbox model", value="GD30/2R")
            reducer_ratio = st.number_input("Gear ratio [-]", value=35.0, step=0.01)
            reducer_eff = st.number_input("Gearbox efficiency [%]", value=96.0, step=0.5)

        with gb_b:
            reducer_max_torque = st.number_input("Maximum output torque [N·m]", value=370.0, step=10.0)
            reducer_radial = st.number_input("Admissible output radial force [N]", value=6300.0, step=100.0)
            reducer_max_power = st.number_input("Maximum input power [kW]", value=1.50, step=0.10)

        st.markdown("#### Motor")
        motor_a, motor_b = st.columns(2)

        with motor_a:
            motor_manufacturer = st.text_input("Motor manufacturer", value="WEG")
            motor_model = st.text_input("Motor model", value="")
            motor_power = st.number_input("Motor rated power [kW]", value=1.50, step=0.10)
            motor_speed = st.number_input("Motor rated speed [rpm]", value=1745.0, step=1.0)

        with motor_b:
            motor_eff = st.number_input("Motor efficiency [%]", value=86.5, step=0.1)
            nominal_freq = st.number_input("Rated frequency [Hz]", value=60.0, step=1.0)
            operating_freq = st.number_input("Operating frequency [Hz]", value=60.0, step=1.0)

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


final_output = calculate_final_output(drive, transmission, conveyor_dp)

with drive_output_col:
    st.markdown("#### Available at conveyor shaft")
    st.metric("Available linear speed", f"{fmt(final_output.linear_speed_m_min, 1)} m/min")
    st.metric("Available shaft torque", f"{fmt(final_output.axis_torque_nm, 1)} N·m")
    st.metric("Available shaft power", f"{fmt(final_output.axis_power_kw, 2)} kW")
    st.metric("Available shaft speed", f"{fmt(final_output.axis_speed_rpm, 1)} rpm")

    if coupling_mode == "Secondary chain transmission":
        st.markdown("##### Secondary transmission check")
        radial_force = final_output.radial_tangential_force_n or 0.0
        st.metric("Tangential force at reducer sprocket", f"{fmt(radial_force, 0)} N")
        st.metric("Admissible reducer radial force", f"{fmt(drive.admissible_radial_force_n, 0)} N")

        if final_output.critical_pitch_diameter_mm is not None:
            st.metric("Theoretical critical pitch diameter", f"{fmt(final_output.critical_pitch_diameter_mm, 1)} mm")

        st.caption(
            "The critical pitch diameter is a theoretical limit with no additional safety factor. "
            "It is not a recommended sprocket diameter."
        )


# STEP 5 ----------------------------------------------------------------------

st.divider()
st.markdown(
    '<div class="section-kicker">Step 5</div>'
    '<div class="section-title">Required vs available</div>',
    unsafe_allow_html=True,
)

speed_error = (
    (final_output.linear_speed_m_min - linear_speed) / linear_speed
    if linear_speed > 0
    else 0.0
)
power_ratio = capacity_ratio(final_output.axis_power_kw, conveyor.required_axis_power_kw)
torque_ratio = capacity_ratio(final_output.axis_torque_nm, conveyor.required_axis_torque_nm)

speed_status, speed_class = status_for_speed(speed_error)
power_status, power_class = status_for_capacity(power_ratio)
torque_status, torque_class = status_for_capacity(torque_ratio)

comparison_rows = [
    {
        "Parameter": "Linear speed",
        "Required": round(linear_speed, 2),
        "Available": round(final_output.linear_speed_m_min, 2),
        "Unit": "m/min",
        "Margin / deviation": f"{speed_error * 100:+.1f}%",
        "Status": speed_status,
    },
    {
        "Parameter": "Power",
        "Required": round(conveyor.required_axis_power_kw, 3),
        "Available": round(final_output.axis_power_kw, 3),
        "Unit": "kW",
        "Margin / deviation": f"{power_ratio:.2f}x",
        "Status": power_status,
    },
    {
        "Parameter": "Torque",
        "Required": round(conveyor.required_axis_torque_nm, 2),
        "Available": round(final_output.axis_torque_nm, 2),
        "Unit": "N·m",
        "Margin / deviation": f"{torque_ratio:.2f}x",
        "Status": torque_status,
    },
]

radial_status = None
radial_class = None

if coupling_mode == "Secondary chain transmission":
    radial_force = final_output.radial_tangential_force_n or 0.0
    radial_ratio = capacity_ratio(drive.admissible_radial_force_n, radial_force)
    radial_status = "OK" if radial_ratio >= 1.0 else "FAIL"
    radial_class = "status-ok" if radial_ratio >= 1.0 else "status-bad"

    comparison_rows.append(
        {
            "Parameter": "Reducer radial / tangential load",
            "Required": round(radial_force, 1),
            "Available": round(drive.admissible_radial_force_n, 1),
            "Unit": "N",
            "Margin / deviation": f"{radial_ratio:.2f}x",
            "Status": radial_status,
        }
    )

summary_cols = st.columns(4 if coupling_mode == "Secondary chain transmission" else 3)

summary_cols[0].markdown(
    f'<div class="engineering-card"><div class="label">Linear speed</div>'
    f'<div class="value">{fmt(linear_speed, 1)} → {fmt(final_output.linear_speed_m_min, 1)} m/min</div>'
    f'<div class="sub"><span class="{speed_class}">{speed_status}</span></div></div>',
    unsafe_allow_html=True,
)
summary_cols[1].markdown(
    f'<div class="engineering-card"><div class="label">Power</div>'
    f'<div class="value">{fmt(conveyor.required_axis_power_kw, 2)} → {fmt(final_output.axis_power_kw, 2)} kW</div>'
    f'<div class="sub"><span class="{power_class}">{power_status}</span></div></div>',
    unsafe_allow_html=True,
)
summary_cols[2].markdown(
    f'<div class="engineering-card"><div class="label">Torque</div>'
    f'<div class="value">{fmt(conveyor.required_axis_torque_nm, 1)} → {fmt(final_output.axis_torque_nm, 1)} N·m</div>'
    f'<div class="sub"><span class="{torque_class}">{torque_status}</span></div></div>',
    unsafe_allow_html=True,
)

if coupling_mode == "Secondary chain transmission":
    radial_force = final_output.radial_tangential_force_n or 0.0
    summary_cols[3].markdown(
        f'<div class="engineering-card"><div class="label">Reducer radial load</div>'
        f'<div class="value">{fmt(radial_force, 0)} → {fmt(drive.admissible_radial_force_n, 0)} N</div>'
        f'<div class="sub"><span class="{radial_class}">{radial_status}</span></div></div>',
        unsafe_allow_html=True,
    )

st.dataframe(
    pd.DataFrame(comparison_rows),
    hide_index=True,
    use_container_width=True,
)


# DETAILS ---------------------------------------------------------------------

with st.expander("Force breakdown and intermediate values"):
    force_rows = [
        ("Top friction force F_top", conveyor.top_friction_n, "N"),
        ("Load inclination force", conveyor.inclination_force_n, "N"),
        ("Acceleration force", conveyor.acceleration_force_n, "N"),
        ("Steady-state resistance", conveyor.regime_force_n, "N"),
        ("Force before drive design factor", conveyor.force_before_design_factor_n, "N"),
    ]

    if return_mode == "Guided return":
        force_rows.insert(1, ("Return friction force F_ret", conveyor.return_friction_n, "N"))
    else:
        force_rows.insert(1, ("Static catenary tension", conveyor.catenary_tension_n or 0.0, "N"))

    st.dataframe(
        pd.DataFrame(force_rows, columns=["Parameter", "Value", "Unit"]),
        hide_index=True,
        use_container_width=True,
    )


st.markdown('<div id="wood-mass-helper"></div>', unsafe_allow_html=True)

with st.expander("Auxiliary carried-mass calculator"):
    density = st.number_input(
        "Material density [kg/m³]",
        min_value=1.0,
        value=1150.0,
        step=10.0,
        key="material_density",
    )

    prism_col, cylinder_col = st.columns(2, gap="large")

    with prism_col:
        st.markdown("**Rectangular prism**")

        if AUXILIARY_PRISM_IMAGE is not None:
            st.image(str(AUXILIARY_PRISM_IMAGE), use_container_width=True)
        else:
            st.warning("Image not found: `auxiliary prism.*` inside `assets/`.")

        prism_inputs = st.columns(3)

        with prism_inputs[0]:
            prism_l1 = st.number_input("Length ℓ1 [m]", value=3.00, step=0.10, key="prism_l1")
        with prism_inputs[1]:
            prism_l2 = st.number_input("Width ℓ2 [m]", value=0.40, step=0.01, key="prism_l2")
        with prism_inputs[2]:
            prism_l3 = st.number_input("Height ℓ3 [m]", value=0.20, step=0.01, key="prism_l3")

        prism_volume, prism_mass = rectangular_mass(
            prism_l2,
            prism_l3,
            prism_l1,
            density,
        )

        st.write(f"Volume: **{fmt(prism_volume, 3)} m³**")
        st.write(f"Mass: **{fmt(prism_mass, 1)} kg**")

    with cylinder_col:
        st.markdown("**Cylinder / log**")

        if AUXILIARY_CYLINDER_IMAGE is not None:
            st.image(str(AUXILIARY_CYLINDER_IMAGE), use_container_width=True)
        else:
            st.warning("Image not found: `auxiliary cylinder.*` inside `assets/`.")

        cylinder_inputs = st.columns(2)

        with cylinder_inputs[0]:
            cylinder_diameter = st.number_input(
                "Diameter Ø [m]",
                value=0.40,
                step=0.01,
                key="cylinder_diameter",
            )

        with cylinder_inputs[1]:
            cylinder_l1 = st.number_input(
                "Length ℓ1 [m]",
                value=3.00,
                step=0.10,
                key="cylinder_l1",
            )

        cylinder_volume, cylinder_mass = cylindrical_mass(
            cylinder_diameter,
            cylinder_l1,
            density,
        )

        st.write(f"Volume: **{fmt(cylinder_volume, 3)} m³**")
        st.write(f"Mass: **{fmt(cylinder_mass, 1)} kg**")


# GLOSSARY --------------------------------------------------------------------

st.divider()
st.markdown(
    '<div class="section-kicker">Reference</div>'
    '<div class="section-title">Variable glossary</div>',
    unsafe_allow_html=True,
)

glossary_rows = [
    {"Variable": "C", "Name": "Center distance", "Description": "Distance between the centers of the conveyor sprockets.", "Unit": "m", "Shown in schematic": "Yes"},
    {"Variable": "Dp", "Name": "Pitch diameter", "Description": "Pitch diameter of the conveyor sprocket.", "Unit": "mm", "Shown in schematic": "Yes"},
    {"Variable": "F_add", "Name": "Additional force", "Description": "Additional external or process force acting against conveyor motion.", "Unit": "N", "Shown in schematic": "Yes"},
    {"Variable": "F_top", "Name": "Top friction force", "Description": "Friction force on the loaded upper strand.", "Unit": "N", "Shown in schematic": "Yes"},
    {"Variable": "F_ret", "Name": "Return friction force", "Description": "Friction force on the guided return strand.", "Unit": "N", "Shown in schematic": "Guided return only"},
    {"Variable": "s", "Name": "Sag", "Description": "Vertical sag of the unsupported return strand.", "Unit": "mm", "Shown in schematic": "Sag return only"},
    {"Variable": "μ_top", "Name": "Top friction coefficient", "Description": "Coefficient of friction used for the loaded upper sliding strand.", "Unit": "-", "Shown in schematic": "No"},
    {"Variable": "μ_ret", "Name": "Return friction coefficient", "Description": "Coefficient of friction used for the guided return strand.", "Unit": "-", "Shown in schematic": "No"},
    {"Variable": "Dp1", "Name": "Reducer sprocket pitch diameter", "Description": "Pitch diameter of the sprocket mounted on the reducer output shaft.", "Unit": "mm", "Shown in schematic": "Reduction only"},
    {"Variable": "Dp2", "Name": "Conveyor-shaft sprocket pitch diameter", "Description": "Pitch diameter of the driven sprocket mounted on the conveyor shaft.", "Unit": "mm", "Shown in schematic": "Reduction only"},
    {"Variable": "ω", "Name": "Angular velocity", "Description": "Angular velocity of the drive sprocket.", "Unit": "rad/s", "Shown in schematic": "Yes"},
    {"Variable": "α", "Name": "Conveyor inclination", "Description": "Inclination angle of the conveyor relative to horizontal.", "Unit": "°", "Shown in schematic": "No"},
]

st.dataframe(
    pd.DataFrame(glossary_rows),
    hide_index=True,
    use_container_width=True,
)

st.markdown(
    """
    <div class="soft-note">
        <b>Load-sharing assumption:</b> force per strand assumes reasonably uniform load distribution between parallel chains. This requires compatible chain lengths, synchronized sprockets, level guides, equivalent tensioning and similar wear between strands.
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "The drive design factor is applied to the calculated force, torque and power demand. "
    "Structural verification of the chain against breaking load must be performed separately."
)
