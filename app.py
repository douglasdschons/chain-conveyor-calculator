"""Calculadora de transportadores de correntes.

Interface compacta em português brasileiro. O equacionamento mecânico permanece
centralizado em src/calculations.py. Imagens originais não são modificadas.
"""
from __future__ import annotations

from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

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
    cv_to_kw,
    cylindrical_mass,
    kw_to_cv,
    rectangular_mass,
    separate_drive_output,
)
from src.localization import format_number, parse_number

st.set_page_config(
    page_title="Calculadora de transportadores de correntes",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def find_asset(name: str) -> Path | None:
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        path = ASSETS_DIR / f"{name}{extension}"
        if path.is_file():
            return path
    if ASSETS_DIR.is_dir():
        for path in ASSETS_DIR.iterdir():
            if path.is_file() and path.stem.casefold() == name.casefold() \
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
    :root{--border:#d9dde4;--header:#eaf2f8;--muted:#667085;--input:#f4f6f8;--result-blue:#163b67}
    .block-container{max-width:1500px;padding:.75rem 1rem 1.5rem}
    header[data-testid="stHeader"]{height:2rem}
    h1{font-size:1.38rem!important;line-height:1.15!important;margin:0!important}
    .section-bar{background:var(--header);border:1px solid var(--border);
      border-radius:5px;padding:.38rem .52rem;margin:.55rem 0 .35rem;
      font-size:.92rem;line-height:1.2rem;font-weight:700}
    .cell-grid{display:grid;border-left:1px solid var(--border);
      border-top:1px solid var(--border);margin-bottom:.3rem}
    .cell{border-right:1px solid var(--border);border-bottom:1px solid var(--border);
      padding:.34rem .46rem;min-width:0;min-height:50px;background:#fff}
    .cell-label,.result-label{font-size:.77rem;color:var(--muted);line-height:1.1rem}
    .cell-value{font-size:.99rem;font-weight:700;color:#1f2937;
      line-height:1.14rem;margin-top:.12rem;overflow-wrap:anywhere}
    .result-value{font-size:.95rem;font-weight:500;color:var(--result-blue);
      line-height:1.14rem;margin-top:.12rem;overflow-wrap:anywhere}
    .result-field{border:1px solid var(--border);border-radius:5px;
      background:#fff;padding:.33rem .45rem;min-height:4rem;box-sizing:border-box}
    .result-field .result-label{color:#344054;min-height:1.56rem}
    div[data-testid="stTextInput"],
    div[data-testid="stSelectbox"]{border:1px solid var(--border);border-radius:5px;
      padding:.28rem .38rem .18rem;background:#fff;box-sizing:border-box}
    .section-note{font-size:.77rem;color:var(--muted);line-height:1.2rem}
    div[data-testid="stVerticalBlock"]{gap:.32rem}
    div[data-testid="stHorizontalBlock"]{gap:.48rem;align-items:flex-start}
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stToggle"] label{font-size:.77rem!important;line-height:1rem!important;margin-bottom:.05rem!important;color:#344054!important}
    div[data-testid="stTextInput"] input{font-size:.86rem!important;
      height:2.18rem!important;min-height:2.18rem!important;
      padding-top:.16rem!important;padding-bottom:.16rem!important;
      background:var(--input)!important}
    div[data-testid="stSelectbox"]>div>div{min-height:2.18rem!important;font-size:.86rem!important;background:var(--input)!important}
    div[data-testid="stExpander"] summary{font-size:.85rem!important;font-weight:600!important}
    .power-label{font-size:.77rem;color:#344054;margin-bottom:.12rem}

    /* Entradas e resultados têm a mesma família e tamanho de fonte. */
    .cell-label,.cell-value,.result-label,.result-value{
      font-family:inherit!important;font-size:.84rem!important;
      font-weight:400!important;color:#000!important}
    div[data-testid="stTextInput"] label p,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stRadio"] label p,
    div[data-testid="stToggle"] label p,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] [data-baseweb="select"],
    div[data-testid="stSelectbox"] [data-baseweb="select"] *,
    .power-label{font-family:inherit!important;font-size:.84rem!important;
      color:#163b67!important;font-weight:700!important}
    @media(max-width:900px){.block-container{padding:.5rem .55rem 1rem}
      .cell-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
    </style>""",
    unsafe_allow_html=True,
)


def fmt(value: float, decimals: int = 1) -> str:
    return format_number(value, decimals)


def section_bar(title: str) -> None:
    st.markdown(f'<div class="section-bar">{escape(title)}</div>', unsafe_allow_html=True)


def cell_grid(items: list[tuple[str, str]], columns: int = 5) -> None:
    css = " ".join("minmax(0,1fr)" for _ in range(columns))
    parts = [f'<div class="cell-grid" style="grid-template-columns:{css}">']
    for label, value in items:
        parts.append(
            f'<div class="cell"><div class="cell-label">{escape(label)}</div>'
            f'<div class="cell-value">{escape(value)}</div></div>'
        )
    st.markdown("".join(parts) + "</div>", unsafe_allow_html=True)


def calculated_field(label: str, value: str) -> None:
    st.markdown(
        f'<div class="result-field"><div class="result-label">{escape(label)}</div>'
        f'<div class="result-value">{escape(value)}</div></div>',
        unsafe_allow_html=True,
    )


def _commit_number(key: str, integer: bool, minimum: float | None,
                   maximum: float | None, callback, args: tuple) -> None:
    try:
        value = parse_number(st.session_state[f"entrada:{key}"], integer)
        if minimum is not None and value < minimum:
            raise ValueError(f"O valor mínimo é {fmt(minimum, 5).rstrip('0').rstrip(',')}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"O valor máximo é {fmt(maximum, 5).rstrip('0').rstrip(',')}.")
    except ValueError as error:
        st.session_state[f"erro:{key}"] = str(error)
        return
    st.session_state.pop(f"erro:{key}", None)
    st.session_state[key] = value
    if callback is not None:
        callback(*args)


def number_input_pt(label: str, min_value=None, max_value=None, value=None,
                    step=None, format=None, key=None, on_change=None, args=(), help=None):
    """Campo de entrada com vírgula decimal, independentemente do navegador."""
    key = key or f"numero:{label}"
    if value is None:
        value = min_value if min_value is not None else 0.0
    integer = isinstance(value, int) and (step is None or isinstance(step, int))
    if format:
        decimals = int(format.split(".")[1][:-1])
    else:
        decimals = max(2, len(str(value).partition(".")[2]),
                       len(str(step or 1).partition(".")[2]))
    if integer:
        decimals = 0
    st.session_state.setdefault(key, value)
    if not format and not integer:
        decimals = max(decimals, len(str(st.session_state[key]).partition(".")[2]))
    text_key = f"entrada:{key}"
    shown_key = f"exibido:{key}"
    if text_key not in st.session_state or st.session_state.get(shown_key) != st.session_state[key]:
        st.session_state[text_key] = format_number(st.session_state[key], decimals, grouping=False)
        st.session_state[shown_key] = st.session_state[key]
    st.text_input(label, key=text_key, help=help, on_change=_commit_number,
                  args=(key, integer, min_value, max_value, on_change, args))
    if st.session_state.get(f"erro:{key}"):
        st.error(f"{label}: {st.session_state[f'erro:{key}']}")
        st.stop()
    return st.session_state[key]


def power_from_kw(prefix: str) -> None:
    st.session_state[f"{prefix}_cv"] = kw_to_cv(st.session_state[f"{prefix}_kw"])


def power_from_cv(prefix: str) -> None:
    st.session_state[f"{prefix}_kw"] = cv_to_kw(st.session_state[f"{prefix}_cv"])


def motor_power_pair(prefix: str, default_kw: float) -> float:
    key_kw, key_cv = f"{prefix}_kw", f"{prefix}_cv"
    st.session_state.setdefault(key_kw, default_kw)
    st.session_state.setdefault(key_cv, kw_to_cv(st.session_state[key_kw]))
    st.markdown('<div class="power-label">Potência nominal do motor</div>',
                unsafe_allow_html=True)
    a, b = st.columns(2, gap="small")
    with a:
        number_input_pt("kW", key=key_kw, min_value=0.0, value=default_kw,
                        step=.1, format="%.3f", on_change=power_from_kw,
                        args=(prefix,))
    with b:
        number_input_pt("cv", key=key_cv, min_value=0.0,
                        value=kw_to_cv(default_kw), step=.1,
                        format="%.3f", on_change=power_from_cv, args=(prefix,))
    return float(st.session_state[key_kw])


def render_schematic(image: Path | None, note: str, half_width: bool = False) -> None:
    if image is None:
        st.warning(note)
    elif half_width:
        # A mesma imagem original ocupa 50% da largura disponível.
        _, image_column, _ = st.columns([1, 2, 1], gap="small")
        with image_column:
            st.image(str(image), width="stretch")
    else:
        st.image(str(image), width="stretch")


st.title("Calculadora de transportadores de correntes")
st.markdown('<div class="section-note">Demanda do sistema · conexão e especificação do acionamento</div>',
            unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1 · DADOS DO SISTEMA
# -----------------------------------------------------------------------------
col_sys, col_scheme = st.columns([1.3, .7], gap="medium")
with col_sys:
    section_bar("1 · DADOS DO SISTEMA")

    geometry = st.columns(3)
    with geometry[0]:
        center_distance_m = number_input_pt(
            "Distância entre centros C [m]", min_value=.01, value=4.5, step=.1
        )
    with geometry[1]:
        conveyor_dp = number_input_pt(
            "Diâmetro primitivo Dp [mm]", min_value=1., value=202.66, step=1.
        )
    with geometry[2]:
        use_inclination = st.toggle("Inclinação", value=False)
        inclination_deg = (number_input_pt("α [°]", value=0., step=1.)
                           if use_inclination else 0.)

    chain_cols = st.columns(3)
    with chain_cols[0]:
        return_mode = st.selectbox(
            "Tipo de retorno", ["Retorno guiado", "Retorno livre com flecha"]
        )
    with chain_cols[1]:
        strands = number_input_pt("Vias de corrente [-]", min_value=1,
                                  value=4, step=1)
    with chain_cols[2]:
        chain_mass_per_m = number_input_pt(
            "Massa linear da corrente [kg/m]", min_value=.01,
            value=7.30, step=.1,
            help="Massa por metro de uma via completa, inclusive corrente tripla quando aplicável."
        )

    if return_mode == "Retorno livre com flecha":
        sag_cols = st.columns(3)
        with sag_cols[0]:
            sag_mm = number_input_pt("Flecha do retorno s [mm]",
                                     min_value=1., value=80., step=5.)
        internal_return_type = "Livre"
    else:
        sag_mm = 80.
        internal_return_type = "Guiado"

    # A linha superior reúne a carga transportada, as correntes do trecho
    # superior, sua soma (massa apoiada), o coeficiente e a força de atrito.
    section_bar("MASSA APOIADA E ATRITO SUPERIOR")
    top_cols = st.columns(5, gap="small")
    with top_cols[0]:
        load_mass = number_input_pt("Carga transportada [kg]", min_value=.01,
                                    value=276., step=10.)
    with top_cols[1]:
        top_mass_slot = st.empty()
    with top_cols[2]:
        supported_mass_slot = st.empty()
    with top_cols[3]:
        mu_top = number_input_pt("Atrito superior μ_top [-]", min_value=0.,
                                 value=.35, step=.01)
    with top_cols[4]:
        top_friction_slot = st.empty()

    # No retorno livre a massa continua participando da inércia, mas não há
    # força de deslizamento sobre guias de retorno.
    section_bar("MASSA E ATRITO NO RETORNO")
    return_cols = st.columns(5, gap="small")
    with return_cols[0]:
        return_mass_slot = st.empty()
    with return_cols[1]:
        if internal_return_type == "Guiado":
            mu_return = number_input_pt("Atrito do retorno μ_ret [-]",
                                        min_value=0., value=.25, step=.01)
        else:
            mu_return = 0.
    with return_cols[2]:
        return_friction_slot = st.empty() if internal_return_type == "Guiado" else None
    with return_cols[3]:
        arc_mass_slot = st.empty()
    with return_cols[4]:
        total_chain_mass_slot = st.empty()

    process_cols = st.columns(3)
    with process_cols[0]:
        additional_force = number_input_pt("Força adicional F_add [N]",
                                           min_value=0., value=0., step=10.)
    with process_cols[1]:
        linear_speed = number_input_pt("Velocidade desejada [m/min]",
                                       min_value=.01, value=35., step=1.)

    dynamics = st.columns(3)
    with dynamics[0]:
        consider_acceleration = st.toggle("Aceleração", value=True)
    with dynamics[1]:
        acceleration_time = (number_input_pt("Tempo de aceleração [s]",
                                              min_value=.01, value=3., step=.5)
                             if consider_acceleration else 0.)

# O callback do campo da seção 4 confirma o valor antes de cada reexecução.
design_factor = st.session_state.get("project_factor", 1.5)

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

with top_mass_slot.container():
    calculated_field("Correntes superiores [kg]", f"{fmt(conveyor.top_chain_mass_kg,2)} kg")
with supported_mass_slot.container():
    calculated_field("Massa apoiada [kg]", f"{fmt(conveyor.top_supported_mass_kg,2)} kg")
with top_friction_slot.container():
    calculated_field("Atrito superior F_top [N]", f"{fmt(conveyor.top_friction_n,1)} N")
with return_mass_slot.container():
    calculated_field("Correntes do retorno [kg]", f"{fmt(conveyor.return_chain_mass_kg,2)} kg")
if return_friction_slot is not None:
    with return_friction_slot.container():
        calculated_field("Atrito do retorno F_ret [N]", f"{fmt(conveyor.return_friction_n,1)} N")
with arc_mass_slot.container():
    calculated_field("Correntes nos arcos [kg]", f"{fmt(conveyor.arc_chain_mass_kg,2)} kg")
with total_chain_mass_slot.container():
    calculated_field("Total das correntes [kg]", f"{fmt(conveyor.total_chain_mass_kg,2)} kg")

with col_scheme:
    section_bar("ESQUEMA DO SISTEMA")
    render_schematic(IMG_RETURN if internal_return_type == "Guiado" else IMG_SAG,
                     "Imagem do esquema do sistema não encontrada.")

section_bar("DEMANDA DO SISTEMA")
demand_items = [
    ("Força de projeto", f"{fmt(conveyor.design_force_n,0)} N"),
    ("Força por via", f"{fmt(conveyor.force_per_strand_n,0)} N"),
    ("Torque no eixo", f"{fmt(conveyor.required_axis_torque_nm,1)} N·m"),
    ("Potência no eixo", f"{fmt(conveyor.required_axis_power_kw,2)} kW"),
    ("Potência", f"{fmt(conveyor.required_axis_power_cv,2)} cv"),
    ("Rotação do eixo", f"{fmt(conveyor.required_axis_speed_rpm,1)} rpm"),
    ("Resistência em regime", f"{fmt(conveyor.regime_force_n,0)} N"),
]
if consider_acceleration:
    demand_items += [
        ("Aceleração", f"{fmt(conveyor.acceleration_m_s2,3)} m/s²"),
        ("Força de aceleração", f"{fmt(conveyor.acceleration_force_n,0)} N"),
    ]
cell_grid(demand_items, columns=5)

# -----------------------------------------------------------------------------
# 2 · CONEXÃO DO ACIONAMENTO
# -----------------------------------------------------------------------------
col_connection, col_connection_image = st.columns([.95, 1.05], gap="medium")
with col_connection:
    section_bar("2 · CONEXÃO DO ACIONAMENTO")
    coupling_mode = st.radio(
        "Conexão", ["Direto", "Transmissão secundária por corrente"],
        horizontal=True,
    )
    if coupling_mode == "Transmissão secundária por corrente":
        internal_coupling = "Transmissão secundária"
        c = st.columns(3)
        with c[0]:
            secondary_dp1 = number_input_pt("Dp1 [mm]", min_value=1.,
                                            value=170., step=1.)
        with c[1]:
            secondary_dp2 = number_input_pt("Dp2 [mm]", min_value=1.,
                                            value=202.66, step=1.)
        with c[2]:
            secondary_eff = number_input_pt("η_sec [%]", min_value=.01,
                                            max_value=100., value=98., step=.5)
    else:
        internal_coupling = "Direto"
        secondary_dp1 = secondary_dp2 = 1.
        secondary_eff = 100.

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
with col_connection:
    cell_grid([
        ("Rotação necessária no redutor", f"{fmt(requirement.required_reducer_speed_rpm,1)} rpm"),
        ("Torque necessário no redutor", f"{fmt(requirement.required_reducer_torque_nm,1)} N·m"),
        ("Potência necessária no redutor", f"{fmt(requirement.required_reducer_power_kw,2)} kW"),
    ], columns=3)
with col_connection_image:
    section_bar("ESQUEMA DO ACIONAMENTO")
    render_schematic(IMG_DIRECT if internal_coupling == "Direto" else IMG_REDUCTION,
                     "Imagem do acionamento não encontrada.", half_width=True)

# -----------------------------------------------------------------------------
# 3 · ACIONAMENTO DISPONÍVEL
# -----------------------------------------------------------------------------
section_bar("3 · ACIONAMENTO DISPONÍVEL")
supply_mode = st.radio(
    "Tipo de acionamento",
    ["Motoredutor completo", "Redutor e motor separados"],
    horizontal=True,
)

if supply_mode == "Motoredutor completo":
    r = st.columns([1, 1, 2, 1])
    with r[0]:
        gm_manufacturer = st.text_input("Fabricante", "IBR")
    with r[1]:
        gm_model = st.text_input("Modelo", "Q090 i40")
    with r[2]:
        gm_motor_power = motor_power_pair("gearmotor", cv_to_kw(3.))
    with r[3]:
        gm_motor_speed = number_input_pt("Rotação do motor [rpm]",
                                         min_value=.01, value=1700., step=1.,
                                         key="gearmotor_rpm")

    r = st.columns(4)
    with r[0]:
        gm_ratio = number_input_pt("Redução", min_value=.001,
                                   value=40., step=.01)
    with r[1]:
        gm_output_speed = number_input_pt("Rotação de saída [rpm]",
                                          min_value=.01, value=42.5, step=1.)
    with r[2]:
        gm_output_torque = number_input_pt("Torque de saída [N·m]",
                                           min_value=.01, value=366.8, step=10.)
    with r[3]:
        gm_radial = number_input_pt("Limite radial [N]", min_value=0.,
                                    value=4580., step=100.)
    gm_service_factor = number_input_pt(
        "Fator de serviço do fabricante [-]", min_value=0.,
        value=1.10, step=.05,
    )
    drive = complete_gearmotor_output(CompleteGearmotorInput(
        manufacturer=gm_manufacturer,
        model=gm_model,
        motor_power_kw=gm_motor_power,
        motor_speed_rpm=gm_motor_speed,
        output_speed_rpm=gm_output_speed,
        total_ratio=gm_ratio,
        output_torque_nm=gm_output_torque,
        admissible_radial_force_n=gm_radial,
        manufacturer_service_factor=gm_service_factor,
    ))
else:
    section_bar("REDUTOR")
    r = st.columns(4)
    with r[0]:
        reducer_manufacturer = st.text_input("Fabricante do redutor", "Geremia")
    with r[1]:
        reducer_model = st.text_input("Modelo do redutor", "GD30/2R")
    with r[2]:
        reducer_ratio = number_input_pt("Redução do redutor", min_value=.001,
                                        value=35., step=.01)
    with r[3]:
        reducer_eff = number_input_pt("Rendimento do redutor η [%]",
                                      min_value=.01, max_value=100., value=96., step=.5)
    r = st.columns(3)
    with r[0]:
        reducer_max_torque = number_input_pt("Torque máximo [N·m]",
                                             min_value=0., value=370., step=10.)
    with r[1]:
        reducer_radial = number_input_pt("Limite radial [N]",
                                         min_value=0., value=6300., step=100.)
    with r[2]:
        reducer_max_power = number_input_pt("Potência máxima de entrada [kW]",
                                            min_value=0., value=1.50, step=.10)

    section_bar("MOTOR")
    r = st.columns([1, 1, 2, 1])
    with r[0]:
        motor_manufacturer = st.text_input("Fabricante do motor", "WEG")
    with r[1]:
        motor_model = st.text_input("Modelo do motor", "")
    with r[2]:
        motor_power = motor_power_pair("separate_motor", 1.5)
    with r[3]:
        motor_speed = number_input_pt("Rotação do motor [rpm]",
                                      min_value=.01, value=1745., step=1.,
                                      key="separate_rpm")
    r = st.columns(3)
    with r[0]:
        motor_eff = number_input_pt("Rendimento do motor η [%]",
                                    min_value=.01, max_value=100., value=86.5, step=.1)
    with r[1]:
        nominal_freq = number_input_pt("Frequência nominal [Hz]",
                                       min_value=.01, value=60., step=1.)
    with r[2]:
        operating_freq = number_input_pt("Frequência de operação [Hz]",
                                         min_value=.01, value=60., step=1.)
    drive = separate_drive_output(SeparateDriveInput(
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
    ))

section_bar("4 · NECESSÁRIO × DISPONÍVEL")
number_input_pt(
    "Fator de projeto do acionamento [-]", min_value=1., value=1.5,
    step=.05, key="project_factor",
    help="Margem aplicada uma única vez à força, torque e potência necessários."
)
final = calculate_final_output(drive, transmission, conveyor_dp)
comparison = [
    ("Velocidade linear [m/min]", linear_speed, final.linear_speed_m_min),
    ("Rotação do eixo [rpm]", conveyor.required_axis_speed_rpm, final.axis_speed_rpm),
    ("Torque no eixo [N·m]", conveyor.required_axis_torque_nm, final.axis_torque_nm),
    ("Potência no eixo [kW]", conveyor.required_axis_power_kw, final.axis_power_kw),
]
rows = []
for label, needed, available in comparison:
    status = "Atende" if available + 1e-9 >= needed else "Não atende"
    rows.append(f"<tr><td>{escape(label)}</td><td>{fmt(needed,2)}</td>"
                f"<td>{fmt(available,2)}</td><td>{status}</td></tr>")
comparison_html = (
    '<table style="width:100%;border-collapse:collapse" border="1" cellpadding="6">'
    '<thead><tr><th>Grandeza</th><th>Necessário</th><th>Disponível</th>'
    '<th>Verificação de capacidade</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
)
st.markdown(comparison_html, unsafe_allow_html=True)
radial_note = "Carga radial: verificação pendente com o fabricante."
if final.radial_tangential_force_n is not None:
    radial_note += (f" Força tangencial Ft = {fmt(final.radial_tangential_force_n,1)} N; "
                    f"limite radial informado = {fmt(drive.admissible_radial_force_n,1)} N. "
                    "Ft não representa a carga radial resultante das duas ramas.")
st.caption(radial_note)
st.caption("Velocidade e rotação: a comparação indica capacidade mínima; "
           "valores superiores exigem ajuste para a velocidade desejada.")


def build_report() -> str:
    def table(items):
        return '<table>' + ''.join(
            '<tr><th>' + escape(str(label)) + '</th><td>' + escape(str(value)) + '</td></tr>'
            for label, value in items) + '</table>'

    # Todos os campos confirmados do formulário, inclusive especificações do motor.
    inputs = []
    for key, value in st.session_state.items():
        if key.startswith("entrada:"):
            label = key.removeprefix("entrada:").removeprefix("numero:")
            inputs.append((label, value))
    inputs += [("Tipo de retorno", return_mode), ("Conexão", coupling_mode),
               ("Tipo de acionamento", supply_mode), ("Inclinação [°]", fmt(inclination_deg,2)),
               ("Aceleração considerada", "Sim" if consider_acceleration else "Não"),
               ("Fator de projeto aplicado", fmt(design_factor,2))]
    if supply_mode == "Motoredutor completo":
        inputs += [("Fabricante", gm_manufacturer), ("Modelo", gm_model)]
    else:
        inputs += [("Fabricante do redutor", reducer_manufacturer), ("Modelo do redutor", reducer_model),
                   ("Fabricante do motor", motor_manufacturer), ("Modelo do motor", motor_model)]
    masses = [("Correntes superiores [kg]", fmt(conveyor.top_chain_mass_kg,2)),
              ("Massa apoiada [kg]", fmt(conveyor.top_supported_mass_kg,2)),
              ("Correntes do retorno [kg]", fmt(conveyor.return_chain_mass_kg,2)),
              ("Correntes nos arcos [kg]", fmt(conveyor.arc_chain_mass_kg,2)),
              ("Total das correntes [kg]", fmt(conveyor.total_chain_mass_kg,2)),
              ("Atrito superior [N]", fmt(conveyor.top_friction_n,2)),
              ("Atrito do retorno [N]", fmt(conveyor.return_friction_n,2)),
              ("Força de inclinação [N]", fmt(conveyor.inclination_force_n,2)),
              ("Força de aceleração [N]", fmt(conveyor.acceleration_force_n,2))]
    reducer = [("Rotação necessária no redutor [rpm]", fmt(requirement.required_reducer_speed_rpm,2)),
               ("Torque necessário no redutor [N·m]", fmt(requirement.required_reducer_torque_nm,2)),
               ("Potência necessária no redutor [kW]", fmt(requirement.required_reducer_power_kw,3))]
    stamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<title>Relatório do transportador</title><style>'
            'body{font:14px Arial,sans-serif;color:#111;max-width:1000px;margin:24px auto}'
            'table{border-collapse:collapse;width:100%;margin:12px 0}'
            'th,td{border:1px solid #ccc;padding:6px;text-align:left}'
            'tr{break-inside:avoid}h2{break-after:avoid}button{padding:12px}'
            '@page{size:A4;margin:15mm}@media print{button{display:none}body{margin:0}}'
            '</style></head><body><button onclick="window.print()">Imprimir / Salvar como PDF</button>'
            '<h1>Calculadora de transportadores de correntes</h1><p>Versão 4 · ' + stamp +
            ' · America/Sao_Paulo</p><h2>Dados e especificações</h2>' + table(inputs) +
            '<h2>Massas e forças</h2>' + table(masses) + '<h2>Demanda do sistema</h2>' +
            table(demand_items) + '<h2>Demanda no redutor</h2>' + table(reducer) +
            '<h2>Necessário × disponível</h2>' + comparison_html + '<p>' + escape(radial_note) +
            '</p><p>Velocidades superiores exigem ajuste. O fator de projeto foi aplicado uma única vez. '
            'A verificação radial permanece pendente com o fabricante.</p></body></html>')


report_html = build_report()
st.download_button("Gerar relatório para impressão", data=report_html,
                   file_name="relatorio_transportador.html", mime="text/html")
st.caption("Abra o relatório no navegador e use Imprimir / Salvar como PDF.")


# -----------------------------------------------------------------------------
# CALCULADORA AUXILIAR: imagens a 50%, funcionalidade preservada
# -----------------------------------------------------------------------------
with st.expander("Massa transportada · cálculo auxiliar"):
    density = number_input_pt("Densidade do material ρ [kg/m³]",
                              min_value=.01, value=600., step=10., key="density")
    left, right = st.columns(2)
    with left:
        section_bar("PRISMA RETANGULAR")
        render_schematic(IMG_PRISM, "Imagem do prisma não encontrada.", half_width=True)
        r = st.columns(3)
        with r[0]:
            p_l1 = number_input_pt("ℓ1 [m]", value=3., step=.1, key="p_l1")
        with r[1]:
            p_l2 = number_input_pt("ℓ2 [m]", value=.4, step=.01, key="p_l2")
        with r[2]:
            p_l3 = number_input_pt("ℓ3 [m]", value=.2, step=.01, key="p_l3")
        p_volume, p_mass = rectangular_mass(p_l2, p_l3, p_l1, density)
        cell_grid([("Volume", f"{fmt(p_volume,3)} m³"),
                   ("Massa", f"{fmt(p_mass,1)} kg")], columns=2)

    with right:
        section_bar("CILINDRO / TORA")
        render_schematic(IMG_CYLINDER, "Imagem do cilindro não encontrada.", half_width=True)
        r = st.columns(2)
        with r[0]:
            c_d = number_input_pt("Ø [m]", value=.4, step=.01, key="c_d")
        with r[1]:
            c_l = number_input_pt("ℓ1 [m]", value=3., step=.1, key="c_l")
        c_volume, c_mass = cylindrical_mass(c_d, c_l, density)
        cell_grid([("Volume", f"{fmt(c_volume,3)} m³"),
                   ("Massa", f"{fmt(c_mass,1)} kg")], columns=2)
