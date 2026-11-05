"""Calculadora de transportadores de correntes.

Interface compacta em português brasileiro. O equacionamento mecânico permanece
centralizado em src/calculations.py. Imagens originais não são modificadas.
"""
from __future__ import annotations

from html import escape
from datetime import datetime, timezone
from math import pi, isclose
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
# NÚCLEO PARAMÉTRICO: cada resultado depende de entradas rastreáveis.
# Dados IBR Q090: somente reduções 30, 40 e 50 são entradas catalogadas.
# Fonte: catálogo IBR Q, página impressa 14 (n1 de referência = 1700 rpm).
# =============================================================================
IBR_Q090 = {
    30.0: dict(pmot_cv=4.0, m2m_nm=396.5, m2nom_nm=418.0, eta_pct=80.0, fr2_n=4100.0),
    40.0: dict(pmot_cv=3.0, m2m_nm=366.8, m2nom_nm=403.0, eta_pct=74.0, fr2_n=4580.0),
    50.0: dict(pmot_cv=2.0, m2m_nm=297.4, m2nom_nm=360.0, eta_pct=72.0, fr2_n=4900.0),
}


def match_ibr_row(ratio: float):
    """Não confundir redução arbitrária com uma combinação comercial catalogada."""
    for key, row in IBR_Q090.items():
        if isclose(ratio, key, rel_tol=0, abs_tol=1e-6):
            return row
    return None


def estimate_reducer(motor_kw: float, motor_rpm: float, ratio: float,
                     efficiency_pct: float) -> tuple[float, float, float]:
    """n2=n1/i, P2=Pmotor*eta, T2=P2*60.000/(2*pi*n2)."""
    if motor_kw <= 0 or motor_rpm <= 0 or ratio <= 0 or not (0 < efficiency_pct <= 100):
        raise ValueError("Motor, rotação e redução precisam ser positivos; 0 < η ≤ 100%.")
    n2 = motor_rpm / ratio
    p2 = motor_kw * efficiency_pct / 100
    m2 = p2 * 60000 / (2*pi*n2)
    return n2, m2, p2


def catalog_ibr_q090(motor_kw: float, motor_rpm: float, ratio: float) -> dict:
    """Escala o torque M2M tabulado para a potência e a rotação informadas.

    Para Pmotor ou n1 diferentes da linha IBR, o resultado é uma aproximação;
    η e o limite de torque não representam curva ensaiada na nova condição.
    """
    row=match_ibr_row(ratio)
    if row is None:
        raise ValueError("Redução não catalogada para Q090 na tabela disponível.")
    if motor_kw <= 0 or motor_rpm <= 0:
        raise ValueError("Potência e rotação do motor devem ser positivas.")
    n2 = motor_rpm / ratio
    m2 = row['m2m_nm'] * (kw_to_cv(motor_kw)/row['pmot_cv']) * (1700.0/motor_rpm)
    # A potência de saída parte de torque e velocidade angular; não calcular
    # novamente com uma eficiência arredondada para evitar inconsistência.
    p2 = m2 * 2*pi*n2 / 60000
    return dict(n2=n2, m2=m2, p2=p2, eta_pct=100*p2/motor_kw,
                eta_catalogue_pct=row['eta_pct'], fr2_n=row['fr2_n'],
                m2nom_nm=row['m2nom_nm'], pmot_cv=row['pmot_cv'],
                fs_manufacturer=row['m2nom_nm']/m2,
                within_pmot=kw_to_cv(motor_kw)<=row['pmot_cv']+1e-9,
                within_m2nom=m2<=row['m2nom_nm']+1e-9)


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
    # As entradas mantêm a geometria da terceira imagem: fabricante, modelo,
    # potência em duas unidades, rpm e fator de serviço; depois i, n2, M2 e FR2.
    gm_top = st.columns([1.0,1.0,2.0,1.05,1.05],gap="small")
    with gm_top[0]:
        gm_manufacturer = st.text_input("Fabricante","IBR")
    with gm_top[1]:
        gm_model = st.text_input("Modelo","Q090")
    with gm_top[2]:
        gm_motor_power = motor_power_pair("gearmotor",cv_to_kw(3.0))
    with gm_top[3]:
        gm_motor_speed = number_input_pt("Rotação nominal do motor [rpm]",
            min_value=.01,value=1700.,step=10.,key="gearmotor_rpm",
            on_change=_sync_manual_speed_from_ratio)
    with gm_top[4]:
        manufacturer_fs_slot = st.empty()

    is_ibr_q090 = (gm_manufacturer.strip().upper() == "IBR"
                    and gm_model.strip().upper().replace(" ","").startswith("Q090"))
    gm_modes = ["Catálogo IBR Q090", "Estimativa por rendimento", "Saída informada"]
    gm_source = st.radio("Origem dos dados de saída",gm_modes,horizontal=True)
    row = st.columns(4,gap="small")
    with row[0]:
        gm_ratio = number_input_pt("Redução i (1:i) [-]",min_value=.001,
                                   value=40.,step=1.,format="%.3f",key="gm_ratio",
                                   on_change=_sync_manual_speed_from_ratio)
    with row[1]:
        gm_n2_slot = st.empty()
    with row[2]:
        gm_m2_slot = st.empty()
    with row[3]:
        gm_radial_slot = st.empty()

    gm_catalog_row = None
    gm_catalog_valid = False
    gm_eff_used = None
    gm_pmot_cv = None
    gm_m2nom = None
    gm_service_factor = None
    gm_mode_detail = ""
    catalog_allowed = gm_source == "Catálogo IBR Q090" and is_ibr_q090
    if catalog_allowed:
        gm_catalog_row = match_ibr_row(gm_ratio)
        gm_catalog_valid = gm_catalog_row is not None
    if gm_source == "Catálogo IBR Q090" and not is_ibr_q090:
        st.warning("O catálogo incorporado corresponde apenas ao fabricante IBR e modelo Q090. "
                   "Aplicando estimativa por rendimento, sem atribuir certificação do catálogo.")

    if gm_catalog_valid:
        result = catalog_ibr_q090(gm_motor_power,gm_motor_speed,gm_ratio)
        gm_output_speed=result['n2']
        gm_output_torque=result['m2']
        gm_output_power=result['p2']
        gm_radial=result['fr2_n']
        gm_service_factor=result['fs_manufacturer']
        gm_eff_used=result['eta_pct']
        gm_m2nom=result['m2nom_nm']
        gm_pmot_cv=result['pmot_cv']
        gm_mode_detail="CATÁLOGO Q090 (linha existente)"
        if not result['within_pmot'] or not result['within_m2nom']:
            st.error("A seleção ultrapassa o motor PMot recomendado ou o torque M2Nom da linha IBR. "
                     "Os resultados não constituem uma seleção aprovada.")
        with row[1]:
            with gm_n2_slot.container():
                calculated_field("Rotação de saída [rpm]",f"{fmt(gm_output_speed,2)} rpm")
        with row[2]:
            with gm_m2_slot.container():
                calculated_field("Torque de saída [N·m]",f"{fmt(gm_output_torque,2)} N·m")
        with row[3]:
            with gm_radial_slot.container():
                calculated_field("FR2 admissível [N]",f"{fmt(gm_radial,0)} N")
        st.caption(f"η tabulado: {fmt(gm_catalog_row['eta_pct'],1)} % · "
                   f"M2Nom: {fmt(gm_m2nom,1)} N·m · PMot: {fmt(gm_pmot_cv,1)} cv. "
                   "Potência e rotação diferentes da linha são aproximações."
        )
    elif gm_source == "Saída informada":
        # O usuário fornece o torque do catálogo escolhido. Não se deve inventar
        # como o torque comercial varia com uma redução ainda não catalogada.
        st.session_state.setdefault('gm_manual_output_rpm',gm_motor_speed/gm_ratio)
        with row[1]:
            with gm_n2_slot.container():
                gm_output_speed = number_input_pt("Rotação de saída [rpm]",
                    min_value=.01,value=gm_motor_speed/gm_ratio,step=1.,
                    key='gm_manual_output_rpm',on_change=_sync_manual_ratio_from_speed)
        with row[2]:
            with gm_m2_slot.container():
                gm_output_torque = number_input_pt("Torque informado [N·m]",
                    min_value=.01,value=366.8,step=10.,key='gm_manual_torque')
        with row[3]:
            with gm_radial_slot.container():
                gm_radial = number_input_pt("Limite radial informado [N]",
                    min_value=0.,value=4580.,step=100.,key='gm_manual_radial')
        with manufacturer_fs_slot.container():
            gm_service_factor = number_input_pt("FS fabricante [-]",
                min_value=0.,value=1.10,step=.05,key="gm_manual_fs")
        gm_output_power = gm_output_torque*2*pi*gm_output_speed/60000
        gm_eff_used=100*gm_output_power/gm_motor_power
        gm_mode_detail="SAÍDA INFORMADA (torque independente do modelo)"
        # Usa os dois campos de forma bidirecional por callback. Se valores foram
        # alterados programaticamente sem passar pelo widget, avisar sem inventar T.
        if abs(gm_motor_speed/gm_ratio/gm_output_speed-1)>0.01:
            st.warning("Dados inconsistentes: n2 deve ser aproximadamente n1/i. "
                       "Edite i ou n2 para sincronizar as entradas.")
        if gm_output_power>gm_motor_power+1e-9:
            st.error("O torque/rotação informados exigem mais potência de saída que a potência "
                     "nominal do motor. Verifique os dados do fabricante.")
        st.caption("Torque e FR2 são dados de entrada independentes do fabricante. "
                   "Alterar i sincroniza n2 e recalcula a potência mecânica. "
                   "**Não é possível deduzir outro torque de catálogo sem dados de rendimento/limites.**")
    else:
        if gm_source == "Catálogo IBR Q090":
            st.warning(f"A redução 1:{fmt(gm_ratio,3)} não consta da tabela Q090 disponível "
                       "(30, 40 e 50). Abaixo, cálculo estimado com rendimento informado, "
                       "sem M2Nom ou FR2 homologados.")
        gm_eff_input = number_input_pt("Rendimento estimado η [%]",
            min_value=.01,max_value=100.,value=74.,step=1.,key='gm_eta_estimada')
        gm_output_speed,gm_output_torque,gm_output_power=estimate_reducer(
            gm_motor_power,gm_motor_speed,gm_ratio,gm_eff_input)
        gm_eff_used=gm_eff_input
        gm_mode_detail="ESTIMATIVA: n2=n1/i, P2=Pmotor×η, M2=P2/ω2"
        with row[1]:
            with gm_n2_slot.container():
                calculated_field("Rotação de saída [rpm]",f"{fmt(gm_output_speed,2)} rpm")
        with row[2]:
            with gm_m2_slot.container():
                calculated_field("Torque estimado [N·m]",f"{fmt(gm_output_torque,2)} N·m")
        with row[3]:
            with gm_radial_slot.container():
                gm_radial = number_input_pt("FR2 informado [N] (0 = não informado)",
                    min_value=0.,value=0.,step=100.,key='gm_radial_estimada')
        st.caption("Se η e Pmotor permanecerem constantes, alterar i modifica n2 e M2, "
                   "mas não P2. η somente varia automaticamente nas linhas catalogadas. "
                   "Uma redução fora do catálogo precisa de verificação do fabricante.")
    if gm_source != "Saída informada":
        with manufacturer_fs_slot.container():
            if gm_service_factor is None:
                calculated_field("FS fabricante [-]","Não disponível")
            else:
                calculated_field("FS fabricante [-]",fmt(gm_service_factor,2))

    drive = complete_gearmotor_output(CompleteGearmotorInput(
        manufacturer=gm_manufacturer,model=gm_model,
        motor_power_kw=gm_motor_power,motor_speed_rpm=gm_motor_speed,
        output_speed_rpm=gm_output_speed,total_ratio=gm_ratio,
        output_torque_nm=gm_output_torque,admissible_radial_force_n=gm_radial,
        manufacturer_service_factor=gm_service_factor or 0.,
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
if supply_mode=='Motoredutor completo' and not gm_catalog_valid and gm_source != 'Saída informada':
    st.warning('Relações de capacidade numéricas baseadas em rendimento estimado. ' 
               'Não validam a existência comercial nem os limites térmicos/mecânicos do conjunto.')
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
            ("Origem dos dados", gm_source),
            ("Potência nominal do motor", f"{fmt(gm_motor_power,3)} kW / {fmt(kw_to_cv(gm_motor_power),3)} cv"),
            ("Rotação nominal do motor", f"{fmt(gm_motor_speed,2)} rpm"),
            ("Relação de redução", fmt(gm_ratio,3)),
            ("Fator de serviço do fabricante", fmt(gm_service_factor,2) if gm_service_factor is not None else "Não informado"),
            ("Critério de cálculo do acionamento",gm_mode_detail),
            ("Rendimento inferido/assumido",f"{fmt(gm_eff_used,2)} %" if gm_eff_used is not None else "Não informado") ]
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
    "Redução: n2=n1/i. Com Pmotor e η constantes, P2=Pmotor×η permanece constante e M2 muda inversamente com n2. "
    "P2 muda quando Pmotor, η ou limites aplicáveis mudam. No catálogo Q090, η depende da redução catalogada.",
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
| Potência do motor (kW ou cv), rotação do motor, i, rendimento | Rotação de saída, torque, potência de saída conforme η, velocidade linear e comparação |
| Linha catalogada Q090 30/40/50 | Rendimento de referência, torque, potência, rotação, FS fabricante, FR2 e comparação |
| Dp1, Dp2, η da corrente secundária | Relação da transmissão, rotação/torque/potência no eixo e no redutor, comparação |
| Torque/FR2 da saída informada | Potência derivada e verificação; FR2 altera somente o limite de carga radial |
""")
    st.caption("Uma variável independente não deve ser modificada artificialmente. "
               "Exemplo: com η e potência do motor constantes, mudar i altera o torque e a "
               "rotação, mas preserva a potência de saída.")

# =============================================================================
# MEMORIAL DE EQUAÇÕES E DEPENDÊNCIAS — valores atuais, sem arredondar internamente
# =============================================================================
with st.expander("Memorial de cálculo · fórmulas e dependências"):
    st.markdown("**1. Massas e retorno**")
    st.latex(r"m_{sup}=N_c q C \quad m_{ret}=N_c qL_{ret} \quad m_{arcos}=N_cq\pi D_p")
    st.caption(f"C={fmt(center_distance_m,2)} m; q={fmt(chain_mass_per_m,2)} kg/m; "
               f"N={int(strands)}; Lret={fmt(conveyor.return_length_m,3)} m; "
               f"m_sup={fmt(conveyor.top_chain_mass_kg,2)} kg; "
               f"m_ret={fmt(conveyor.return_chain_mass_kg,2)} kg; "
               f"m_arcos={fmt(conveyor.arc_chain_mass_kg,2)} kg")
    st.markdown("**2. Resistências em regime (sem aceleração)**")
    st.latex(r"F_{sup}=\mu_{sup}(m_{carga}+m_{sup})g\cos\alpha")
    st.latex(r"F_{ret}=\mu_{ret}m_{ret}g\cos\alpha \quad (\mathrm{guiado})")
    st.latex(r"F_{reg}=F_{sup}+F_{ret}+m_{carga}g\sin\alpha+F_{adicional}")
    st.caption(f"F_sup={fmt(conveyor.top_friction_n,2)} N; F_ret={fmt(conveyor.return_friction_n,2)} N; "
               f"F_reg={fmt(conveyor.regime_force_n,2)} N")
    st.markdown("**3. Aceleração e demanda base**")
    st.latex(r"a=\frac{v/60}{t_a}, \quad m_{mov}=m_{carga}+m_{correntes}, \quad F_a=m_{mov}a")
    st.latex(r"F_{base}=F_{reg}+F_a, \quad M_{base}=F_{base}D_p/2, \quad P_{base}=F_{base}v_{m/s}/1000")
    st.latex(r"n_{eixo}=\frac{v_{m/min}}{\pi D_p}, \quad P=\frac{2\pi n M}{60000}")
    st.caption(f"a={fmt(conveyor.acceleration_m_s2,4)} m/s²; F_a={fmt(conveyor.acceleration_force_n,2)} N; "
               f"F_base={fmt(conveyor.force_before_design_factor_n,2)} N; "
               f"M_base={fmt(conveyor.required_axis_torque_nm,2)} N·m; "
               f"P_base={fmt(conveyor.required_axis_power_kw,3)} kW; "
               f"n={fmt(conveyor.required_axis_speed_rpm,2)} rpm")
    st.markdown("**4. Fator de serviço aplicado somente à demanda**")
    st.latex(r"F_{FS}=FS\,F_{base},\quad M_{FS}=FS\,M_{base},\quad P_{FS}=FS\,P_{base}")
    st.caption(f"FS={fmt(service_factor,2)}; M_FS={fmt(corrected_torque_nm,2)} N·m; "
               f"P_FS={fmt(corrected_power_kw,3)} kW")
    st.markdown("**5. Transmissão e motoredutor**")
    st.latex(r"i_{sec}=\frac{D_{p2}}{D_{p1}},\quad n_{eixo}=n_2/i_{sec},\quad M_{eixo}=M_2 i_{sec}\eta_{sec}")
    st.latex(r"i=\frac{n_1}{n_2},\quad P_2=P_{motor}\eta_{red},\quad M_2=\frac{60000P_2}{2\pi n_2}")
    st.caption(f"Conexão={coupling_mode}; redução secundária={fmt(requirement.ratio,3)}; "
               f"n disponível={fmt(final_output.axis_speed_rpm,2)} rpm; "
               f"M disponível={fmt(final_output.axis_torque_nm,2)} N·m; "
               f"P disponível={fmt(final_output.axis_power_kw,3)} kW")
    st.markdown("**6. Comparação**")
    st.latex(r"R=\frac{disponivel}{requerido\ com\ FS},\quad margem=(R-1)100\%")
    st.caption("A capacidade do catálogo é uma condição de seleção, não uma relação que se "
               "possa extrapolar para qualquer redução. A análise não inclui explicitamente "
               "inércia rotacional, choques transitórios ou resistência estrutural da corrente.")

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
