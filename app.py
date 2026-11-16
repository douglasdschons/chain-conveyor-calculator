"""Calculadora de transportadores de correntes.

Interface compacta em português brasileiro. O equacionamento mecânico permanece
centralizado em src/calculations.py. Imagens originais não são modificadas.
"""
from __future__ import annotations

from html import escape
from datetime import datetime, timezone
from math import pi, cos, radians
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
    /* Saídas calculadas: rótulo e valor em preto, sem negrito, iguais. */
    .cell-label,.cell-value,.result-label,.result-value{
      font-size:.84rem;font-weight:400;color:#202124;line-height:1.14rem;
      overflow-wrap:anywhere}
    .cell-value,.result-value{margin-top:.12rem}
    .result-field{border:1px solid var(--border);border-radius:5px;
      background:#fff;padding:.33rem .45rem;min-height:4rem;box-sizing:border-box}
    .result-field .result-label{min-height:1.56rem}
    /* Entradas editáveis: rótulo e valor no mesmo azul, em negrito. */
    div[data-testid="stTextInput"],
    div[data-testid="stSelectbox"]{border:1px solid #9db2ca;border-radius:5px;
      padding:.28rem .38rem .18rem;background:#fff;box-sizing:border-box}
    .section-note{font-size:.77rem;color:var(--muted);line-height:1.2rem}
    div[data-testid="stVerticalBlock"]{gap:.32rem}
    div[data-testid="stHorizontalBlock"]{gap:.48rem;align-items:flex-start}
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stToggle"] label,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] [data-baseweb="select"]{
      font-size:.84rem!important;font-weight:700!important;
      line-height:1.14rem!important;color:var(--result-blue)!important}
    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stRadio"] label,
    div[data-testid="stToggle"] label{margin-bottom:.05rem!important}
    div[data-testid="stTextInput"] input{
      height:2.18rem!important;min-height:2.18rem!important;
      padding-top:.16rem!important;padding-bottom:.16rem!important;
      background:var(--input)!important;
      -webkit-text-fill-color:var(--result-blue)!important}
    div[data-testid="stSelectbox"] [data-baseweb="select"] *,
    div[data-testid="stTextInput"] label *,
    div[data-testid="stSelectbox"] label *,
    div[data-testid="stRadio"] label *,
    div[data-testid="stToggle"] label *{
      color:var(--result-blue)!important;font-weight:700!important;font-size:.84rem!important}
    div[data-testid="stSelectbox"]>div>div{
      min-height:2.18rem!important;background:var(--input)!important}
    div[data-testid="stExpander"] summary{font-size:.85rem!important;font-weight:600!important}
    .power-label{font-size:.84rem;font-weight:700;color:var(--result-blue);margin-bottom:.12rem}
    .comparison-scroll{width:100%;overflow-x:auto;margin-top:.3rem}
    .comparison-table{border-collapse:collapse;width:100%;min-width:790px;table-layout:auto}
    .comparison-table th,.comparison-table td{
      border:1px solid var(--border);padding:.44rem .52rem;text-align:left;
      font-size:.84rem;font-weight:400;color:#202124;vertical-align:middle}
    .comparison-table th{background:var(--header);font-weight:600}
    .comparison-table td.calc-fail{color:#b42318!important;font-weight:700!important;background:#fff1f1}
    .comparison-table td.calc-warn{color:#9a6700!important;font-weight:600!important}
    .comparison-table td.calc-pass{color:#202124}
    .caution-text{font-size:.80rem;color:#9a6700}
    .formula-row{font-size:.80rem;color:#202124}
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



# =============================================================================
# COMPARAÇÃO DE CAPACIDADES. Os valores informados são tratados como entradas
# independentes do fabricante; não existe consulta ou estimativa de catálogo.
# =============================================================================
def ratio_metrics(available: float, required: float, speed: bool = False):
    """Métrica numérica e semântica; a UI não decide com texto formatado."""
    if required <= 0:
        return None, None, "REVISÃO"
    ratio = available/required
    margin = (ratio-1)*100
    if ratio < 1-1e-9:
        state = "ABAIXO DA VELOCIDADE" if speed else "NÃO ATENDE"
    elif speed and ratio > 1.05:
        state = "AJUSTAR VELOCIDADE"
    else:
        state = "ATENDE"
    return ratio,margin,state


def _sync_manual_speed_from_ratio() -> None:
    """Usuário alterou i: a saída manual segue a cinemática n2=n1/i."""
    rpm = float(st.session_state.get('gearmotor_rpm',1700.0))
    ratio = float(st.session_state.get('gm_ratio',40.0))
    if rpm>0 and ratio>0:
        st.session_state['gm_manual_output_rpm'] = rpm/ratio


def _sync_manual_ratio_from_speed() -> None:
    """Usuário alterou n2: a razão cinemática passa a i=n1/n2."""
    rpm = float(st.session_state.get('gearmotor_rpm',1700.0))
    n2 = float(st.session_state.get('gm_manual_output_rpm',42.5))
    if rpm>0 and n2>0:
        st.session_state['gm_ratio'] = rpm/n2

st.title("Calculadora de transportadores de correntes")
st.markdown('<div class="section-note">Demanda do sistema · cálculo paramétrico · especificação do acionamento</div>',
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
                                 value=.25, step=.01)
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
        additional_force = number_input_pt("Força adicional contrária F_add [N]",
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
    design_factor=1.0,  # Demanda física sem margem; o FS da aplicação é aplicado só na seção 4.
))

with top_mass_slot.container():
    calculated_field("Correntes superiores [kg]", f"{fmt(conveyor.top_chain_mass_kg,2)} kg")
with supported_mass_slot.container():
    calculated_field("Massa total superior [kg]", f"{fmt(conveyor.top_supported_mass_kg,2)} kg")
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
    ("Força requerida (base)", f"{fmt(conveyor.design_force_n,0)} N"),
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
    # Campos em um único bloco, sem seleção de origem e sem catálogo embutido.
    # As duas potências permanecem sincronizadas, mas os dados de saída são
    # informados pelo usuário (torque e limite radial não são inferidos).
    st.session_state.setdefault("gearmotor_kw", cv_to_kw(3.0))
    st.session_state.setdefault("gearmotor_cv", kw_to_cv(st.session_state["gearmotor_kw"]))

    gm_top = st.columns(6, gap="small")
    with gm_top[0]:
        gm_manufacturer = st.text_input("Fabricante", "IBR")
    with gm_top[1]:
        gm_model = st.text_input("Modelo", "Q090")
    with gm_top[2]:
        gm_motor_power = number_input_pt(
            "Potência nominal do motor [kW]", min_value=.001,
            value=cv_to_kw(3.0), step=.1, format="%.3f", key="gearmotor_kw",
            on_change=power_from_kw, args=("gearmotor",))
    with gm_top[3]:
        number_input_pt(
            "Potência nominal do motor [cv]", min_value=.001,
            value=3.0, step=.1, format="%.3f", key="gearmotor_cv",
            on_change=power_from_cv, args=("gearmotor",))
    # Captura a variável controlada após ambas as entradas.
    gm_motor_power = float(st.session_state["gearmotor_kw"])
    with gm_top[4]:
        gm_motor_speed = number_input_pt(
            "Rotação nominal do motor [rpm]", min_value=.01,
            value=1700., step=10., key="gearmotor_rpm",
            on_change=_sync_manual_speed_from_ratio)
    with gm_top[5]:
        gm_service_factor = number_input_pt(
            "FS fabricante [-]", min_value=0., value=1.10,
            step=.05, key="gm_manual_fs")

    gm_bottom = st.columns(4, gap="small")
    with gm_bottom[0]:
        gm_ratio = number_input_pt(
            "Redução i (1:i) [-]", min_value=.001, value=40.,
            step=1., format="%.3f", key="gm_ratio",
            on_change=_sync_manual_speed_from_ratio)
    # n2 e i são sincronizados em ambos os sentidos, sem sobrescrever M2.
    st.session_state.setdefault("gm_manual_output_rpm", gm_motor_speed / gm_ratio)
    with gm_bottom[1]:
        gm_output_speed = number_input_pt(
            "Rotação de saída [rpm]", min_value=.01,
            value=gm_motor_speed / gm_ratio, step=1.,
            key="gm_manual_output_rpm", on_change=_sync_manual_ratio_from_speed)
    with gm_bottom[2]:
        gm_output_torque = number_input_pt(
            "Torque informado [N·m]", min_value=.01,
            value=366.8, step=10., key="gm_manual_torque")
    with gm_bottom[3]:
        gm_radial = number_input_pt(
            "Limite radial informado [N]", min_value=0.,
            value=4580., step=100., key="gm_manual_radial")

    gm_output_power = gm_output_torque * 2 * pi * gm_output_speed / 60000
    gm_eff_used = (100 * gm_output_power / gm_motor_power
                   if gm_motor_power > 0 else None)
    gm_mode_detail = "DADOS DE SAÍDA INFORMADOS PELO USUÁRIO"
    if abs(gm_motor_speed / gm_ratio / gm_output_speed - 1) > 0.01:
        st.warning("Inconsistência entre n1, i e n2. Confira os dados informados.")
    if gm_output_power > gm_motor_power + 1e-9:
        st.error("Os valores informados de torque e rotação exigem potência "
                 "de saída superior à potência nominal do motor.")
    st.caption("A redução e a rotação de saída são sincronizadas (n₂ = n₁/i). "
               "Torque e limite radial são dados informados do fabricante; "
               "a potência mecânica de saída é calculada por P₂ = M₂·2πn₂/60.000.")

    drive = complete_gearmotor_output(CompleteGearmotorInput(
        manufacturer=gm_manufacturer, model=gm_model,
        motor_power_kw=gm_motor_power, motor_speed_rpm=gm_motor_speed,
        output_speed_rpm=gm_output_speed, total_ratio=gm_ratio,
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

# Potência, rotação e torque de saída são derivados da mesma condição física.
# A transmissão secundária propaga essas capacidades para o eixo transportador.
preview_output = calculate_final_output(drive, transmission, conveyor_dp)
cell_grid([
    ("Rotação disponível no redutor",f"{fmt(drive.reducer_output_speed_rpm,2)} rpm"),
    ("Torque disponível no redutor",f"{fmt(drive.reducer_output_torque_nm,2)} N·m"),
    ("Potência disponível no redutor",f"{fmt(drive.reducer_output_power_kw,3)} kW"),
    ("Velocidade disponível no transportador",f"{fmt(preview_output.linear_speed_m_min,2)} m/min"),
],columns=4)

# -----------------------------------------------------------------------------
# 4 · DEMANDA BASE × FATOR DE SERVIÇO × DEMANDA CORRIGIDA
# -----------------------------------------------------------------------------
section_bar("4 · DEMANDA, FATOR DE SERVIÇO E COMPARAÇÃO")
comparison_columns = st.columns([1.10, .80, 1.10], gap="medium")
with comparison_columns[0]:
    st.markdown("**REQUERIDO PELO SISTEMA**")
    cell_grid([
        ("Força total", f"{fmt(conveyor.force_before_design_factor_n,2)} N"),
        ("Força por via (sem FS)", f"{fmt(conveyor.force_per_strand_n,2)} N"),
        ("Torque no eixo", f"{fmt(conveyor.required_axis_torque_nm,2)} N·m"),
        ("Potência no eixo", f"{fmt(conveyor.required_axis_power_kw,3)} kW"),
        ("Rotação no eixo", f"{fmt(conveyor.required_axis_speed_rpm,2)} rpm"),
    ], columns=1)
with comparison_columns[1]:
    st.markdown("**FATOR DE SERVIÇO**")
    service_factor = number_input_pt(
        "FS da aplicação [-]", min_value=1.0, value=1.0,
        step=.05, key="application_service_factor",
        help=("Multiplica uma única vez a demanda base de força, torque e potência. "
              "Não modifica velocidade, rotação ou massas e não é o fs do fabricante."),
    )
    st.caption("FS = 1,00: sem margem adicional. A margem é aplicada somente "
               "às grandezas de esforço e potência.")

corrected_force_n = conveyor.force_before_design_factor_n * service_factor
corrected_strand_force_n = conveyor.force_per_strand_n * service_factor
corrected_torque_nm = conveyor.required_axis_torque_nm * service_factor
corrected_power_kw = conveyor.required_axis_power_kw * service_factor
corrected_power_cv = kw_to_cv(corrected_power_kw)
# A transmissão secundária é avaliada também com a exigência corrigida.
corrected_reducer_requirement = calculate_secondary_requirement(
    conveyor.required_axis_speed_rpm,
    corrected_torque_nm,
    corrected_power_kw,
    transmission,
)
with comparison_columns[2]:
    st.markdown("**REQUERIDO COM FS**")
    cell_grid([
        ("Força total", f"{fmt(corrected_force_n,2)} N"),
        ("Força por via", f"{fmt(corrected_strand_force_n,2)} N"),
        ("Torque no eixo", f"{fmt(corrected_torque_nm,2)} N·m"),
        ("Potência no eixo", f"{fmt(corrected_power_kw,3)} kW"),
        ("Rotação no eixo", f"{fmt(conveyor.required_axis_speed_rpm,2)} rpm"),
    ], columns=1)

# Linhas: a relação é calculada sobre a demanda corrigida, nunca sobre texto.
final_output = calculate_final_output(drive, transmission, conveyor_dp)
comparison_data = [
    ("Velocidade linear",linear_speed,final_output.linear_speed_m_min,"m/min",True),
    ("Rotação do eixo",conveyor.required_axis_speed_rpm,final_output.axis_speed_rpm,"rpm",True),
    ("Torque no eixo",corrected_torque_nm,final_output.axis_torque_nm,"N·m",False),
    ("Potência no eixo",corrected_power_kw,final_output.axis_power_kw,"kW",False),
]
compare_rows=[]
compare_numeric=[]
for label,required,available,unit,is_speed in comparison_data:
    r,m,state=ratio_metrics(available,required,speed=is_speed)
    compare_numeric.append((label,required,available,r,m,state,is_speed))
    compare_rows.append((label,f"{fmt(required,2)} {unit}",f"{fmt(available,2)} {unit}",
                         fmt(r,3) if r is not None else "—",
                         f"{fmt(m,1)} %" if m is not None else "—",state))
if internal_coupling != 'Direto':
    compare_rows.append(("Carga radial do redutor","Não calculada",
                         f"Limite: {fmt(drive.admissible_radial_force_n,0)} N",
                         "—","—","REVISÃO"))
    compare_numeric.append(("Carga radial do redutor",None,None,None,None,"REVISÃO",False))
st.markdown("**CAPACIDADE DISPONÍVEL × DEMANDA COM FS**")
ths=("Parâmetro","Requerido com FS","Disponível","R = disp./req.","Margem","Situação")
html=['<div class="comparison-scroll"><table class="comparison-table"><thead><tr>']
for head in ths:
    html.append('<th>'+escape(head)+'</th>')
html.append('</tr></thead><tbody>')
for row,(label,req,avail,r,m,state) in zip(compare_numeric,compare_rows):
    cls='calc-fail' if row[3] is not None and row[3]<1-1e-9 else ('calc-warn' if row[5] not in ('ATENDE','OK') else 'calc-pass')
    html.append('<tr>')
    for idx,value in enumerate((label,req,avail,r,m,state)):
        html.append('<td'+(' class="'+cls+'"' if idx>=3 else '')+'>'+escape(str(value))+'</td>')
    html.append('</tr>')
html.append('</tbody></table></div>')
st.markdown(''.join(html),unsafe_allow_html=True)
st.caption('R = disponível / requerido com FS. R < 1: os valores R, margem e situação ficam em vermelho. '
           'Velocidade acima da meta em mais de 5% também exige ajuste; potência e torque são critérios distintos.')
if internal_coupling != 'Direto':
    st.caption('Carga radial real pendente: Ft não é a resultante das tensões dos dois ramos. ' 
               'Confirmar força radial e ponto de aplicação com fabricante.')

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# RELATÓRIO DE DIMENSIONAMENTO — HTML autônomo, pronto para impressão A4.
# Não exige dependências adicionais nem acesso ao servidor após o download.
# -----------------------------------------------------------------------------
def build_print_report(sections: list[tuple[str, list[tuple[str, str]]]],
                       comparison: list[tuple[str, str, str, str, str, str]],
                       observations: list[str]) -> str:
    """Gera um retrato estático dos resultados, escapando todos os dados exibidos."""
    generated_utc = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    body = []
    for title, rows in sections:
        body.append(f"<section><h2>{escape(title)}</h2><table><tbody>")
        for label, value in rows:
            body.append(f"<tr><th scope='row'>{escape(str(label))}</th>"
                        f"<td>{escape(str(value))}</td></tr>")
        body.append("</tbody></table></section>")
    body.append("<section><h2>4 · NECESSÁRIO × DISPONÍVEL</h2>"
                "<table><thead><tr><th>Parâmetro</th><th>Necessário c/ FS</th>"
                "<th>Disponível</th><th>R</th><th>Margem</th><th>Situação</th>"
                "</tr></thead><tbody>")
    for row in comparison:
        try:
            r_value = float(str(row[3]).replace('.','').replace(',','.'))
            failure = r_value < 1
        except ValueError:
            failure = False
        body.append("<tr>" + "".join(
            "<td" + (' class="fail"' if failure and i>=3 else '') + ">" + escape(str(field)) + "</td>"
            for i,field in enumerate(row)) + "</tr>")
    body.append("</tbody></table></section>")
    body.append("<section><h2>Premissas e limitações</h2><ul>")
    for note in observations:
        body.append(f"<li>{escape(note)}</li>")
    body.append("</ul></section>")
    content = "\n".join(body)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório — Transportador de correntes</title>
<style>
@page {{ size: A4 portrait; margin: 15mm; }}
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Arial, Helvetica, sans-serif; color:#172536; margin:0 auto;
        max-width:980px; padding:20px 24px; font-size:11pt; background:#fff; }}
header {{ border-bottom:2px solid #24496f; padding-bottom:12px; margin-bottom:16px; }}
h1 {{ margin:0 0 8px; font-size:21pt; color:#163b67; }}
h2 {{ margin:18px 0 8px; font-size:12.5pt; color:#163b67;
      background:#edf3f8; padding:6px 8px; }}
.meta {{ color:#4b5665; font-size:9pt; }}
.controls {{ margin-bottom:18px; }}
button {{ padding:10px 16px; background:#163b67; color:white; border:0;
         border-radius:5px; font:600 11pt Arial,sans-serif; cursor:pointer; }}
table {{ border-collapse:collapse; width:100%; table-layout:fixed; }}
th,td {{ border:1px solid #cdd5df; padding:6px 9px; text-align:left;
         vertical-align:top; word-break:break-word; }}
th {{ background:#f5f7f9; font-weight:600; }}
section table tbody th {{ width:55%; }}
li {{ margin:5px 0; line-height:1.4; }}
.fail {{ color:#b42318; font-weight:700; background:#fff1f1; }}
section {{ break-inside:avoid-page; page-break-inside:avoid; }}
footer {{ font-size:9pt; color:#5a6673; border-top:1px solid #ddd;
          margin-top:22px; padding-top:10px; }}
@media print {{
  body {{ padding:0; max-width:none; }}
  .controls {{ display:none !important; }}
  h2 {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  a {{ color:inherit; text-decoration:none; }}
}}
</style>
</head>
<body>
<div class="controls"><button type="button" onclick="window.print()">Imprimir / Salvar como PDF</button></div>
<header>
  <h1>Relatório de dimensionamento — Transportador de correntes</h1>
  <div class="meta">Gerado em: {escape(generated_utc)} · Valores registrados na geração do relatório</div>
</header>
{content}
<footer>Memória de resultados para conferência técnica. Não substitui a validação do projeto nem a seleção do fabricante.</footer>
</body>
</html>"""


report_sections = [
    ("1 · Dados do sistema", [
        ("Distância entre centros C", f"{fmt(center_distance_m,2)} m"),
        ("Diâmetro primitivo Dp", f"{fmt(conveyor_dp,2)} mm"),
        ("Inclinação", f"{fmt(inclination_deg,2)} °"),
        ("Tipo de retorno", return_mode),
        *(([("Flecha do retorno", f"{fmt(sag_mm,1)} mm")]
           if internal_return_type == "Livre" else [])),
        ("Vias de corrente", f"{int(strands)}"),
        ("Massa linear da corrente por via", f"{fmt(chain_mass_per_m,2)} kg/m"),
        ("Carga transportada", f"{fmt(load_mass,2)} kg"),
        ("Coeficiente de atrito superior", fmt(mu_top,3)),
        *(([("Coeficiente de atrito de retorno", fmt(mu_return,3))]
           if internal_return_type == "Guiado" else [])),
        ("Força adicional F_add", f"{fmt(additional_force,2)} N"),
        ("Velocidade desejada", f"{fmt(linear_speed,2)} m/min"),
        ("Aceleração habilitada", "Sim" if consider_acceleration else "Não"),
        *(([("Tempo de aceleração", f"{fmt(acceleration_time,2)} s")]
           if consider_acceleration else [])),
        ("Fator de serviço da aplicação", fmt(service_factor,2)),
    ]),
    ("Massas e resistências", [
        ("Correntes superiores", f"{fmt(conveyor.top_chain_mass_kg,2)} kg"),
        ("Massa total superior (carga + correntes)", f"{fmt(conveyor.top_supported_mass_kg,2)} kg"),
        ("Correntes do retorno", f"{fmt(conveyor.return_chain_mass_kg,2)} kg"),
        ("Correntes nos arcos", f"{fmt(conveyor.arc_chain_mass_kg,2)} kg"),
        ("Massa total das correntes", f"{fmt(conveyor.total_chain_mass_kg,2)} kg"),
        ("Força de atrito superior F_top", f"{fmt(conveyor.top_friction_n,2)} N"),
        ("Força de atrito de retorno F_ret", f"{fmt(conveyor.return_friction_n,2)} N"),
        ("Resistência em regime", f"{fmt(conveyor.regime_force_n,2)} N"),
        ("Força de aceleração", f"{fmt(conveyor.acceleration_force_n,2)} N"),
    ]),
    ("Demanda do acionamento", [
        ("Força requerida sem FS", f"{fmt(conveyor.force_before_design_factor_n,2)} N"),
        ("Força por via (sem FS)", f"{fmt(conveyor.force_per_strand_n,2)} N"),
        ("Rotação requerida no eixo", f"{fmt(conveyor.required_axis_speed_rpm,2)} rpm"),
        ("Torque requerido sem FS", f"{fmt(conveyor.required_axis_torque_nm,2)} N·m"),
        ("Potência requerida sem FS", f"{fmt(conveyor.required_axis_power_kw,3)} kW / {fmt(conveyor.required_axis_power_cv,3)} cv"),
        ("Força corrigida com FS", f"{fmt(corrected_force_n,2)} N"),
        ("Torque corrigido com FS", f"{fmt(corrected_torque_nm,2)} N·m"),
        ("Potência corrigida com FS", f"{fmt(corrected_power_kw,3)} kW / {fmt(corrected_power_cv,3)} cv"),
    ]),
    ("2 · Conexão mecânica", [
        ("Conexão", coupling_mode),
        *(([("Dp1 — roda do redutor", f"{fmt(secondary_dp1,2)} mm"),
            ("Dp2 — roda do transportador", f"{fmt(secondary_dp2,2)} mm"),
            ("Rendimento da transmissão secundária", f"{fmt(secondary_eff,2)} %")]
           if internal_coupling != "Direto" else [])),
        ("Rotação requerida na saída do redutor", f"{fmt(requirement.required_reducer_speed_rpm,2)} rpm"),
        ("Torque base na saída do redutor", f"{fmt(requirement.required_reducer_torque_nm,2)} N·m"),
        ("Potência base na saída do redutor", f"{fmt(requirement.required_reducer_power_kw,3)} kW"),
        ("Torque com FS na saída do redutor", f"{fmt(corrected_reducer_requirement.required_reducer_torque_nm,2)} N·m"),
        ("Potência com FS na saída do redutor", f"{fmt(corrected_reducer_requirement.required_reducer_power_kw,3)} kW"),
    ]),
    ("3 · Acionamento disponível", [
        ("Tipo", supply_mode),
        *(([("Fabricante do motoredutor", gm_manufacturer),
            ("Modelo do motoredutor", gm_model),
            ("Potência nominal do motor", f"{fmt(gm_motor_power,3)} kW / {fmt(kw_to_cv(gm_motor_power),3)} cv"),
            ("Rotação nominal do motor", f"{fmt(gm_motor_speed,2)} rpm"),
            ("Relação de redução", fmt(gm_ratio,3)),
            ("Fator de serviço do fabricante", fmt(gm_service_factor,2) if gm_service_factor is not None else "Não informado"),
            ("Critério de cálculo do acionamento",gm_mode_detail),
            ("Potência de saída implícita / potência do motor",f"{fmt(gm_eff_used,2)} %" if gm_eff_used is not None else "Não informado") ]
           if supply_mode == "Motoredutor completo" else [
            ("Fabricante do redutor", reducer_manufacturer),
            ("Modelo do redutor", reducer_model),
            ("Redução do redutor", fmt(reducer_ratio,3)),
            ("Rendimento do redutor", f"{fmt(reducer_eff,2)} %"),
            ("Torque máximo do redutor informado", f"{fmt(reducer_max_torque,2)} N·m"),
            ("Potência máxima de entrada", f"{fmt(reducer_max_power,3)} kW"),
            ("Fabricante do motor", motor_manufacturer),
            ("Modelo do motor", motor_model),
            ("Potência nominal do motor", f"{fmt(motor_power,3)} kW / {fmt(kw_to_cv(motor_power),3)} cv"),
            ("Rotação nominal do motor", f"{fmt(motor_speed,2)} rpm"),
            ("Rendimento informado do motor", f"{fmt(motor_eff,2)} %"),
            ("Frequência nominal / de operação", f"{fmt(nominal_freq,2)} / {fmt(operating_freq,2)} Hz"),
        ])),
        ("Rotação disponível na saída do redutor", f"{fmt(drive.reducer_output_speed_rpm,2)} rpm"),
        ("Torque disponível na saída do redutor", f"{fmt(drive.reducer_output_torque_nm,2)} N·m"),
        ("Potência disponível na saída do redutor", f"{fmt(drive.reducer_output_power_kw,3)} kW"),
        ("Força radial admissível informada", f"{fmt(drive.admissible_radial_force_n,1)} N"),
    ]),
]
report_notes = [
    "Dependências: alterar massa, atrito ou distância entre centros propaga as alterações para as forças e demanda. "
    "Alterar Dp também altera a massa dos arcos, a rotação requerida e a velocidade linear disponível.",
    "Saída informada: n2=n1/i; M2 e FR2 são dados independentes fornecidos pelo usuário. "
    "P2 = 2πn2M2/60000 (kW) e muda com n2 quando M2 é mantido constante. "
    "Não é possível obter automaticamente o torque nominal de outra redução sem dados do fabricante.",
    "Equações: m_sup=N×q×C; m_ret=N×q×C (guiado); m_arcos=N×q×π×Dp; m_móvel=m_carga+m_correntes.",
    "Atrito: F_sup=μ_sup×(m_carga+m_sup)×g×cos(α); F_ret=μ_ret×m_ret×g×cos(α).",
    "Demanda: F_base=F_regime+F_aceleração; F_aceleração=m_móvel×v/t_aceleração; M_base=F_base×Dp/2; P_base=F_base×v/1000.",
    "FS da aplicação: F_corr=FS×F_base; M_corr=FS×M_base; P_corr=FS×P_base. Velocidade e rotação não se alteram.",
    "A demanda física é calculada sem fator: a coluna de correção multiplica força, torque e potência uma única vez pelo FS da aplicação.",
    "O FS da aplicação é distinto do fator de serviço informado pelo catálogo do fabricante.",
    "Atrito superior calculado por F_top = μ_top × (m_carga + m_correntes_superiores) × g × cos(α).",
    "No retorno guiado, F_ret = μ_ret × m_correntes_retorno × g × cos(α).",
    "A massa das correntes nos arcos integra a massa móvel, mas não acrescenta atrito dos trechos retos.",
    "Capacidade com R = disponível / requerido com FS: R ≥ 1,00 atende ao critério quantitativo; abaixo de 1,00 não atende. O usuário observa a margem sem fator de aprovação arbitrário.",
    "A rotação e a velocidade não são multiplicadas pelo FS. O desvio de velocidade é verificado contra a faixa de ±5%.",
    "Os resultados são estimativas de dimensionamento, não uma validação de resistência estrutural, vida dos mancais ou compatibilidade térmica.",
]
if internal_coupling != "Direto":
    report_notes.append("A carga radial real na transmissão secundária não está determinada; a força tangencial não equivale à carga radial resultante.")
else:
    report_notes.append("No acionamento direto, as reações nos mancais e eventuais cargas de acoplamento precisam ser verificadas separadamente.")

report_html = build_print_report(report_sections, compare_rows, report_notes)
st.download_button(
    "Gerar relatório para impressão",
    data=report_html.encode("utf-8"),
    file_name="relatorio_transportador_correntes.html",
    mime="text/html",
    help="Baixa um relatório HTML independente. Abra no navegador e clique em Imprimir / Salvar como PDF.",
    key="report_download",
)
st.caption("O relatório registra os valores atuais. Abra o arquivo HTML no navegador e selecione Imprimir / Salvar como PDF.")

# =============================================================================
# MAPA DO GRAFO DE DEPENDÊNCIAS: só alteram grandezas fisicamente dependentes.
# =============================================================================
with st.expander("Mapa de dependências · entradas e efeitos"):
    st.markdown("""| Entrada alterada | Consequências recalculadas |
|---|---|
| C, quantidade de vias, massa linear | Massas dos trechos, atritos, massa móvel, aceleração, força, torque e potência requeridos |
| Dp do transportador | Massa nos arcos, massa móvel, aceleração, torque, rotação necessária e velocidade linear disponível |
| Carga, μ superior, μ retorno, tipo de retorno, inclinação, F adicional | Forças resistentes, força de projeto base, torque e potência requeridos |
| Velocidade desejada, tempo de aceleração, aceleração ligada/desligada | Aceleração, força total, potência, rotação requerida e comparação |
| FS da aplicação | Somente força, torque e potência requeridos corrigidos, relação e margem (não altera velocidade) |
| Potência nominal do motor (kW ou cv) | Atualiza a unidade vinculada e a verificação de coerência de potência; não inventa torque ou rendimento do redutor |
| Rotação do motor, i ou rotação de saída | Sincronizam n2 = n1/i; atualizam a potência derivada de n2 e M2, a velocidade linear e a comparação |
| Torque de saída informado | Atualiza potência de saída, capacidade e comparação; não altera a redução |
| FS do fabricante, limite radial informado | Atualizam apenas os respectivos dados e verificações pertinentes |
| Dp1, Dp2, η da corrente secundária | Relação da transmissão, rotação/torque/potência no eixo e no redutor, comparação |
| Torque/FR2 da saída informada | Potência derivada e verificação; FR2 altera somente o limite de carga radial |
""")
    st.caption("No modo de saída informada, o torque não é recalculado por hipótese: "
               "ao mudar i, n2 e a potência implícita mudam para o torque informado. "
               "A especificação de um novo torque deve vir do fabricante.")

# =============================================================================
# MEMORIAL DE EQUAÇÕES E DEPENDÊNCIAS — valores atuais, sem arredondar internamente
# =============================================================================
# =============================================================================
# MEMORIAL PARAMÉTRICO: sequência causal, fórmulas + valores em tempo real.
# Os resultados vêm de calculate_conveyor, não de cálculos paralelos para a UI.
# =============================================================================
def memorial_number(value: float, decimals: int = 2) -> str:
    """Decimal brasileiro em LaTeX; não arredonda os valores de cálculo."""
    number = format_number(value, decimals, grouping=False)
    return number.replace(",", "{,}")


def memorial_step(title: str, symbolic: str, substituted: str,
                  observation: str | None = None) -> None:
    st.markdown(f"**{title}**")
    st.latex(symbolic)
    st.latex(substituted)
    if observation:
        st.caption(observation)


with st.expander("Memorial de cálculo · fórmulas e dependências"):
    m = memorial_number
    d_m = conveyor_dp / 1000.0
    s_m = sag_mm / 1000.0
    v_m_s = linear_speed / 60.0
    g = 9.81
    # Força normal do trecho superior; a resistência resulta do modelo real.
    n_top = conveyor.top_supported_mass_kg * g * cos(radians(inclination_deg))
    n_ret = conveyor.return_chain_mass_kg * g * cos(radians(inclination_deg))
    omega_req = 2.0 * pi * conveyor.required_axis_speed_rpm / 60.0

    st.markdown(
        "A sequência abaixo começa nas entradas geométricas e operacionais, "
        "calcula as massas, obtém as forças resistentes, acrescenta a aceleração "
        "e chega à **força, rotação, torque e potência exigidos no eixo**. "
        "Todos os números são atualizados com os valores informados na calculadora. "
        "As substituições numéricas são exibidas arredondadas; as operações usam precisão completa."
    )
    st.caption(
        "Fluxo lógico: C, Dp, q, vias e tipo de retorno → massas das correntes → "
        "massa apoiada + atritos → resistência em regime → aceleração → "
        "força requerida → torque, rotação e potência → FS → "
        "requisito do redutor → relação entre disponível e requerido."
    )
    st.markdown("### 0 · Dados necessários e conversões")
    st.markdown("**Entradas do dimensionamento**")
    st.caption(
        f"Geometria: C = {fmt(center_distance_m,2)} m; Dp = {fmt(conveyor_dp,2)} mm; "
        f"vias Nc = {int(strands)}; massa linear por via q = {fmt(chain_mass_per_m,2)} kg/m; "
        f"retorno = {return_mode}."
    )
    st.caption(
        f"Operação: carga mc = {fmt(load_mass,2)} kg; μsup = {fmt(mu_top,3)}; "
        f"μret = {fmt(mu_return,3) if internal_return_type == 'Guiado' else 'não aplicável'}; "
        f"inclinação α = {fmt(inclination_deg,2)}°; "
        f"força adicional = {fmt(additional_force,2)} N; "
        f"velocidade = {fmt(linear_speed,2)} m/min; "
        f"aceleração = {'ligada' if consider_acceleration else 'desligada'}"
        + (f"; tempo ta = {fmt(acceleration_time,2)} s." if consider_acceleration else ".")
    )
    memorial_step(
        "0.1 · Diâmetro primitivo em metros (comprimentos e torque)",
        r"D_p[\mathrm{m}]=\frac{D_p[\mathrm{mm}]}{1000}",
        rf"D_p=\frac{{{m(conveyor_dp,2)}}}{{1000}}=\boxed{{{m(d_m,5)}\ \mathrm{{m}}}}"
    )
    memorial_step(
        "0.2 · Velocidade linear em m/s (aceleração e potência)",
        r"v[\mathrm{m/s}]=\frac{v[\mathrm{m/min}]}{60}",
        rf"v=\frac{{{m(linear_speed,2)}}}{{60}}=\boxed{{{m(v_m_s,5)}\ \mathrm{{m/s}}}}"
    )
    st.caption("Adota-se aceleração gravitacional g = 9,81 m/s². "
               "O ângulo informado em graus é convertido internamente para radianos nas funções trigonométricas.")

    st.markdown("### 1 · Geometria → massas das correntes")
    memorial_step(
        "1.1 · Massa das correntes no trecho superior",
        r"m_{sup}=N_c\,q\,C",
        rf"m_{{sup}}={int(strands)}\cdot{m(chain_mass_per_m,2)}\cdot{m(center_distance_m,2)}"
        rf"=\boxed{{{m(conveyor.top_chain_mass_kg,2)}\ \mathrm{{kg}}}}",
        "q é a massa linear de UMA via; a quantidade Nc multiplica a massa do trecho."
    )
    if internal_return_type == "Guiado":
        memorial_step(
            "1.2 · Comprimento reto do retorno guiado",
            r"L_{ret}=C",
            rf"L_{{ret}}={m(center_distance_m,2)}=\boxed{{{m(conveyor.return_length_m,3)}\ \mathrm{{m}}}}",
            "No retorno guiado os dois trechos retos têm o mesmo comprimento."
        )
    else:
        memorial_step(
            "1.2 · Comprimento aproximado do retorno livre com flecha",
            r"s[\mathrm{m}]=s[\mathrm{mm}]/1000\qquad "
            r"L_{ret}\approx C+\frac{8s^2}{3C}",
            rf"L_{{ret}}\approx {m(center_distance_m,3)}+"
            rf"\frac{{8\cdot {m(s_m,4)}^2}}{{3\cdot {m(center_distance_m,3)}}}"
            rf"=\boxed{{{m(conveyor.return_length_m,4)}\ \mathrm{{m}}}}",
            "Comprimento aproximado pela parábola; a flecha é convertida para metros."
        )
    memorial_step(
        "1.3 · Massa das correntes no trecho inferior",
        r"m_{ret}=N_c\,q\,L_{ret}",
        rf"m_{{ret}}={int(strands)}\cdot{m(chain_mass_per_m,2)}\cdot{m(conveyor.return_length_m,4)}"
        rf"=\boxed{{{m(conveyor.return_chain_mass_kg,2)}\ \mathrm{{kg}}}}"
    )
    memorial_step(
        "1.4 · Massa das correntes nos arcos das rodas",
        r"L_{arcos}=\pi D_p\qquad m_{arcos}=N_c\,q\,\pi D_p",
        rf"m_{{arcos}}={int(strands)}\cdot{m(chain_mass_per_m,2)}\cdot\pi\cdot{m(d_m,5)}"
        rf"=\boxed{{{m(conveyor.arc_chain_mass_kg,2)}\ \mathrm{{kg}}}}",
        "Hipótese do modelo: duas semicircunferências de mesmo diâmetro primitivo, "
        "equivalentes a uma circunferência por via."
    )
    memorial_step(
        "1.5 · Massa total das correntes",
        r"m_{corr}=m_{sup}+m_{ret}+m_{arcos}",
        rf"m_{{corr}}={m(conveyor.top_chain_mass_kg,2)}+{m(conveyor.return_chain_mass_kg,2)}"
        rf"+{m(conveyor.arc_chain_mass_kg,2)}"
        rf"=\boxed{{{m(conveyor.total_chain_mass_kg,2)}\ \mathrm{{kg}}}}"
    )

    st.markdown("### 2 · Massas apoiadas → normais → forças de atrito")
    memorial_step(
        "2.1 · Massa total sobre as guias superiores",
        r"m_{total,sup}=m_c+m_{sup}",
        rf"m_{{total,sup}}={m(load_mass,2)}+{m(conveyor.top_chain_mass_kg,2)}"
        rf"=\boxed{{{m(conveyor.top_supported_mass_kg,2)}\ \mathrm{{kg}}}}",
        "Esta é uma MASSA em kg, não o peso. O peso correspondente é uma força em N."
    )
    memorial_step(
        "2.2 · Força normal no trecho superior",
        r"N_{sup}=m_{total,sup}\,g\cos\alpha",
        rf"N_{{sup}}={m(conveyor.top_supported_mass_kg,2)}\cdot9{{,}}81\cdot"
        rf"\cos({m(inclination_deg,2)}^\circ)"
        rf"=\boxed{{{m(n_top,2)}\ \mathrm{{N}}}}",
        "Na direção normal ao plano utiliza-se cosseno da inclinação."
    )
    memorial_step(
        "2.3 · Atrito do trecho superior",
        r"F_{sup}=\mu_{sup}\,N_{sup}",
        rf"F_{{sup}}={m(mu_top,3)}\cdot{m(n_top,2)}"
        rf"=\boxed{{{m(conveyor.top_friction_n,2)}\ \mathrm{{N}}}}"
    )
    if internal_return_type == "Guiado":
        memorial_step(
            "2.4 · Normal nas guias inferiores",
            r"N_{ret}=m_{ret}\,g\cos\alpha",
            rf"N_{{ret}}={m(conveyor.return_chain_mass_kg,2)}\cdot9{{,}}81\cdot"
            rf"\cos({m(inclination_deg,2)}^\circ)"
            rf"=\boxed{{{m(n_ret,2)}\ \mathrm{{N}}}}"
        )
        memorial_step(
            "2.5 · Atrito do retorno guiado",
            r"F_{ret}=\mu_{ret}\,N_{ret}",
            rf"F_{{ret}}={m(mu_return,3)}\cdot{m(n_ret,2)}"
            rf"=\boxed{{{m(conveyor.return_friction_n,2)}\ \mathrm{{N}}}}"
        )
    else:
        st.markdown("**2.4 · Retorno livre: sem atrito das guias inferiores**")
        st.latex(r"F_{ret}=0\quad\, (\mathrm{retorno\ sem\ guias})")
        st.caption("A massa da corrente inferior continua no sistema móvel. "
                   "Sua tração pela flecha é estimada a seguir, mas não é somada à força de atrito.")
        memorial_step(
            "2.5 · Tração aproximada da corrente suspensa, por via",
            r"w=qg\qquad H\approx\frac{wC^2}{8s}\qquad "
            r"V\approx\frac{wC}{2}\qquad T=\sqrt{H^2+V^2}",
            rf"w={m(chain_mass_per_m,2)}\cdot9{{,}}81={m(chain_mass_per_m*g,2)}\ \mathrm{{N/m}},\quad\,"
            rf"H={m(conveyor.catenary_horizontal_n or 0,2)}\ \mathrm{{N}},\quad\,"
            rf"V={m(conveyor.catenary_vertical_n or 0,2)}\ \mathrm{{N}},\quad\,"
            rf"T=\boxed{{{m(conveyor.catenary_tension_n or 0,2)}\ \mathrm{{N}}}}",
            "Aproximação parabólica; esta tração não é igual à força motriz."
        )
    memorial_step(
        "2.6 · Componente resistente associada à inclinação",
        r"F_{incl}=m_c\,g\sin\alpha",
        rf"F_{{incl}}={m(load_mass,2)}\cdot9{{,}}81\cdot\sin({m(inclination_deg,2)}^\circ)"
        rf"=\boxed{{{m(conveyor.inclination_force_n,2)}\ \mathrm{{N}}}}",
        "O modelo atual considera o peso da carga transportada nessa parcela; "
        "não soma explicitamente outras resistências por inclinação das correntes."
    )
    memorial_step(
        "2.7 · Resistência total em regime",
        r"F_{reg}=F_{sup}+F_{ret}+F_{incl}+F_{add}",
        rf"F_{{reg}}={m(conveyor.top_friction_n,2)}+{m(conveyor.return_friction_n,2)}"
        rf"+{m(conveyor.inclination_force_n,2)}+{m(additional_force,2)}"
        rf"=\boxed{{{m(conveyor.regime_force_n,2)}\ \mathrm{{N}}}}",
        "É a força para manter velocidade constante; não inclui a aceleração."
    )

    st.markdown("### 3 · Resistência em regime + aceleração → força exigida")
    memorial_step(
        "3.1 · Massa total acelerada",
        r"m_{mov}=m_c+m_{corr}",
        rf"m_{{mov}}={m(load_mass,2)}+{m(conveyor.total_chain_mass_kg,2)}"
        rf"=\boxed{{{m(conveyor.moving_mass_kg,2)}\ \mathrm{{kg}}}}",
        "Inclui as correntes nos arcos; não inclui inércia rotacional de rodas, eixos e redutor."
    )
    if consider_acceleration:
        memorial_step(
            "3.2 · Aceleração linear média, partindo do repouso",
            r"a=\frac{\Delta v}{\Delta t}=\frac{v}{t_a}",
            rf"a=\frac{{{m(v_m_s,5)}}}{{{m(acceleration_time,2)}}}"
            rf"=\boxed{{{m(conveyor.acceleration_m_s2,5)}\ \mathrm{{m/s^2}}}}"
        )
    else:
        st.markdown("**3.2 · Aceleração desativada**")
        st.latex(r"a=0\ \mathrm{m/s^2}")
    memorial_step(
        "3.3 · Força para acelerar a massa móvel",
        r"F_a=m_{mov}\,a",
        rf"F_a={m(conveyor.moving_mass_kg,2)}\cdot{m(conveyor.acceleration_m_s2,5)}"
        rf"=\boxed{{{m(conveyor.acceleration_force_n,2)}\ \mathrm{{N}}}}"
    )
    memorial_step(
        "3.4 · Força total requerida (sem fator de serviço)",
        r"F_{req}=F_{reg}+F_a",
        rf"F_{{req}}={m(conveyor.regime_force_n,2)}+{m(conveyor.acceleration_force_n,2)}"
        rf"=\boxed{{{m(conveyor.force_before_design_factor_n,2)}\ \mathrm{{N}}}}"
    )
    memorial_step(
        "3.5 · Força média por via de corrente",
        r"F_{via}=\frac{F_{req}}{N_c}",
        rf"F_{{via}}=\frac{{{m(conveyor.force_before_design_factor_n,2)}}}{{{int(strands)}}}"
        rf"=\boxed{{{m(conveyor.force_per_strand_n,2)}\ \mathrm{{N}}}}",
        "Assume distribuição uniforme entre as vias; não determina as tensões internas de cada elo."
    )

    st.markdown("### 4 · Força + diâmetro + velocidade → torque, rotação e potência")
    memorial_step(
        "4.1 · Raio primitivo e torque exigido no eixo",
        r"r=\frac{D_p}{2}\qquad M_{req}=F_{req}\,r",
        rf"M_{{req}}={m(conveyor.force_before_design_factor_n,2)}\cdot\frac{{{m(d_m,5)}}}{{2}}"
        rf"=\boxed{{{m(conveyor.required_axis_torque_nm,2)}\ \mathrm{{N\,m}}}}",
        "Torque exigido pelo esforço tangencial no diâmetro primitivo informado."
    )
    memorial_step(
        "4.2 · Rotação exigida no eixo (v em m/min; Dp em m)",
        r"v_{m/min}=\pi D_p\,n\qquad n_{req}=\frac{v_{m/min}}{\pi D_p}",
        rf"n_{{req}}=\frac{{{m(linear_speed,2)}}}{{\pi\cdot{m(d_m,5)}}}"
        rf"=\boxed{{{m(conveyor.required_axis_speed_rpm,2)}\ \mathrm{{rpm}}}}"
    )
    memorial_step(
        "4.3 · Velocidade angular correspondente",
        r"\omega=\frac{2\pi n_{req}}{60}",
        rf"\omega=\frac{{2\pi\cdot{m(conveyor.required_axis_speed_rpm,3)}}}{{60}}"
        rf"=\boxed{{{m(omega_req,5)}\ \mathrm{{rad/s}}}}"
    )
    memorial_step(
        "4.4 · Potência mecânica exigida por força e velocidade",
        r"P_{req}[\mathrm{kW}]=\frac{F_{req}\,v[\mathrm{m/s}]}{1000}",
        rf"P_{{req}}=\frac{{{m(conveyor.force_before_design_factor_n,2)}\cdot{m(v_m_s,5)}}}{{1000}}"
        rf"=\boxed{{{m(conveyor.required_axis_power_kw,4)}\ \mathrm{{kW}}}}"
    )
    memorial_step(
        "4.5 · Conferência independente: torque × velocidade angular",
        r"P_{req}=\frac{M_{req}\,\omega}{1000}=\frac{2\pi n_{req}M_{req}}{60000}",
        rf"P_{{req}}=\frac{{{m(conveyor.required_axis_torque_nm,3)}\cdot{m(omega_req,5)}}}{{1000}}"
        rf"\approx\boxed{{{m(conveyor.required_axis_power_kw,4)}\ \mathrm{{kW}}}}",
        "Os dois métodos devem produzir o mesmo valor, salvo arredondamento na exibição."
    )
    memorial_step(
        "4.6 · Conversão de potência de kW para cv",
        r"P_{cv}=\frac{P_{kW}}{0{,}73549875}",
        rf"P_{{cv}}=\frac{{{m(conveyor.required_axis_power_kw,5)}}}{{0{{,}}73549875}}"
        rf"=\boxed{{{m(conveyor.required_axis_power_cv,4)}\ \mathrm{{cv}}}}"
    )

    st.markdown("### 5 · Fator de serviço da aplicação (fora da demanda física)")
    memorial_step(
        "5.1 · Demanda corrigida pelo FS escolhido",
        r"F_{FS}=FS\,F_{req}\quad\, F_{via,FS}=FS\,F_{via}\quad\, "
        r"M_{FS}=FS\,M_{req}\quad\, P_{FS}=FS\,P_{req}",
        rf"FS={m(service_factor,3)}\ \Rightarrow\ "
        rf"F_{{FS}}={m(corrected_force_n,2)}\ \mathrm{{N}},\quad\,"
        rf"M_{{FS}}={m(corrected_torque_nm,2)}\ \mathrm{{N\,m}},\quad\,"
        rf"P_{{FS}}={m(corrected_power_kw,4)}\ \mathrm{{kW}}",
        "A velocidade e a rotação não são multiplicadas pelo FS. "
        "O FS da aplicação não equivale ao fator de serviço informado pelo fabricante."
    )

    st.markdown("### 6 · Conexão do acionamento → requisito na saída do redutor")
    if internal_coupling == "Direto":
        memorial_step(
            "6.1 · Acionamento direto",
            r"n_{red,req}=n_{req}\quad\, M_{red,req}=M_{FS}\quad\, P_{red,req}=P_{FS}",
            rf"n_{{red,req}}={m(corrected_reducer_requirement.required_reducer_speed_rpm,2)}\ \mathrm{{rpm}},\quad\,"
            rf"M_{{red,req}}={m(corrected_reducer_requirement.required_reducer_torque_nm,2)}\ \mathrm{{N\,m}},\quad\,"
            rf"P_{{red,req}}={m(corrected_reducer_requirement.required_reducer_power_kw,4)}\ \mathrm{{kW}}"
        )
    else:
        eta_sec = secondary_eff / 100.0
        memorial_step(
            "6.1 · Relação e rendimento da transmissão secundária",
            r"i_{sec}=\frac{D_{p2}}{D_{p1}}\qquad \eta_{sec}=\frac{\eta_{sec,\%}}{100}",
            rf"i_{{sec}}=\frac{{{m(secondary_dp2,2)}}}{{{m(secondary_dp1,2)}}}"
            rf"={m(requirement.ratio,4)},\quad\,\eta_{{sec}}={m(eta_sec,4)}"
        )
        memorial_step(
            "6.2 · Rotação, torque e potência requeridos no redutor",
            r"n_{red,req}=i_{sec}\,n_{req}\quad\, "
            r"M_{red,req}=\frac{M_{FS}}{i_{sec}\eta_{sec}}\quad\, "
            r"P_{red,req}=\frac{P_{FS}}{\eta_{sec}}",
            rf"n_{{red,req}}={m(corrected_reducer_requirement.required_reducer_speed_rpm,2)}\ \mathrm{{rpm}},\quad\,"
            rf"M_{{red,req}}={m(corrected_reducer_requirement.required_reducer_torque_nm,2)}\ \mathrm{{N\,m}},\quad\,"
            rf"P_{{red,req}}={m(corrected_reducer_requirement.required_reducer_power_kw,4)}\ \mathrm{{kW}}"
        )

    st.markdown("### 7 · Acionamento informado → capacidade e comparação")
    if supply_mode == "Motoredutor completo":
        memorial_step(
            "7.1 · Rotação de saída pela redução informada",
            r"i=\frac{n_1}{n_2}\qquad n_2=\frac{n_1}{i}",
            rf"n_2=\frac{{{m(gm_motor_speed,2)}}}{{{m(gm_ratio,3)}}}"
            rf"={m(gm_output_speed,2)}\ \mathrm{{rpm}}",
            "O valor de torque M₂ é informado pelo usuário e não é estimado a partir da redução."
        )
    else:
        st.markdown("**7.1 · Redutor e motor separados**")
        st.caption("O modelo operacional utiliza a rotação do motor ajustada pela razão "
                   "entre frequências, a redução do redutor, o rendimento e os limites de entrada/torque informados. "
                   "A potência elétrica de entrada não é calculada pela potência nominal do eixo do motor.")
        st.latex(r"n_{m,op}=n_{m,nom}\frac{f_{op}}{f_{nom}}\qquad n_2=\frac{n_{m,op}}{i}")
        st.latex(r"P_{m,lim}=\min(P_{m,modelo},P_{red,entrada,max})")
        st.latex(r"M_2=\min\left(\frac{9550P_{m,lim}}{n_{m,op}}\,i\eta_{red},M_{red,max}\right)")
        st.caption(f"n₂ = {fmt(drive.reducer_output_speed_rpm,2)} rpm; "
                   f"M₂ = {fmt(drive.reducer_output_torque_nm,2)} N·m; "
                   f"P₂ = {fmt(drive.reducer_output_power_kw,3)} kW")
    memorial_step(
        "7.2 · Potência mecânica disponível na saída do redutor",
        r"P_{2}=\frac{2\pi n_2M_2}{60000}",
        rf"P_2=\frac{{2\pi\cdot{m(drive.reducer_output_speed_rpm,3)}\cdot{m(drive.reducer_output_torque_nm,3)}}}{{60000}}"
        rf"=\boxed{{{m(drive.reducer_output_power_kw,4)}\ \mathrm{{kW}}}}"
    )
    if internal_coupling != "Direto":
        memorial_step(
            "7.3 · Capacidade disponível transferida ao eixo do transportador",
            r"n_{disp}=\frac{n_2}{i_{sec}}\quad\, "
            r"M_{disp}=M_2i_{sec}\eta_{sec}\quad\, "
            r"P_{disp}=\frac{2\pi n_{disp}M_{disp}}{60000}",
            rf"n_{{disp}}={m(final_output.axis_speed_rpm,2)}\ \mathrm{{rpm}},\quad\,"
            rf"M_{{disp}}={m(final_output.axis_torque_nm,2)}\ \mathrm{{N\,m}},\quad\,"
            rf"P_{{disp}}={m(final_output.axis_power_kw,4)}\ \mathrm{{kW}}"
        )
    memorial_step(
        "7.4 · Velocidade linear disponível",
        r"v_{disp}=\pi D_p\,n_{disp}",
        rf"v_{{disp}}=\pi\cdot{m(d_m,5)}\cdot{m(final_output.axis_speed_rpm,3)}"
        rf"=\boxed{{{m(final_output.linear_speed_m_min,2)}\ \mathrm{{m/min}}}}"
    )
    st.markdown("**7.5 · Relação de capacidade, margem e situação**")
    st.latex(r"R=\frac{X_{disp}}{X_{req,FS}}\qquad "
             r"\mathrm{Margem}=(R-1)\,100\%")
    for label, req, avail, ratio, margin, status, is_speed in compare_numeric:
        if ratio is None:
            st.caption(f"{label}: verificação não determinada ({status}).")
        else:
            st.caption(f"{label}: requerido = {fmt(req,3)}; disponível = {fmt(avail,3)}; "
                       f"R = {fmt(ratio,3)}; margem = {fmt(margin,1)}%; situação = {status}.")
    st.caption("R < 1: capacidade abaixo da demanda. Para velocidade, também se verifica "
               "excesso sobre a velocidade desejada. Uma razão de torque adequada não "
               "substitui a verificação da velocidade e das condições de serviço.")

    st.markdown("### 8 · Premissas e limites do modelo")
    st.markdown(
        "- A massa linear informada corresponde a uma via completa de corrente. "
        "A massa dos arcos pressupõe duas rodas de mesmo diâmetro primitivo.\n"
        "- As forças de atrito usam o coeficiente equivalente informado para as superfícies. "
        "O modelo não representa individualmente a resistência de cada rolete ou articulação.\n"
        "- A aceleração considera massa translacional; não adiciona inércia rotacional, "
        "impactos transitórios nem perdas não especificadas.\n"
        "- A força por via admite repartição uniforme entre as correntes paralelas.\n"
        "- O modelo de inclinação atual usa somente a massa da carga transportada "
        "na componente F_incl.\n"
        "- Torque nominal, capacidade térmica, tensões internas das correntes, "
        "reação radial nos mancais e adequação normativa exigem verificação independente."
    )

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
