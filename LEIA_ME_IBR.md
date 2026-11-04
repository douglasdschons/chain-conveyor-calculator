# Chain Conveyor Calculator — Pré-seleção IBR Q (04/11/2026)

## Objetivo da atualização

Expandir a versão anterior da calculadora com um modo de fornecimento **"IBR Q catalogue"** no bloco `3 · PROVIDED DRIVE`. Esta versão incorpora as modificações anteriores de massa/atrito, campos bidirecionais kW↔cv e memória de cálculo. Não depende de substituir ou editar qualquer imagem da pasta `assets`.

**O repositório GitHub não foi alterado.** O branch público `main` verificado em 04/11/2026 permanecia com os arquivos-base anteriores à atualização de massa e à seleção IBR; portanto, a distribuição contém o `app.py` e `src/calculations.py` **completos**. Usar ambos do pacote, não misturar com versões antigas.

## Instalação

1. Descompactar o ZIP em uma pasta temporária.
2. Copiar `app.py`, `src/calculations.py` e `src/ibr_catalog.py` para as mesmas posições do repositório local.
3. Copiar os testes `tests/test_*.py` para a pasta `tests`, substituindo os homônimos.
4. **Não apagar a pasta existente `assets`.** Manter `requirements.txt` e os demais arquivos do repositório.
5. Executar no terminal, na raiz do repositório:

   ```powershell
   python -m unittest discover -s tests -v
   streamlit run app.py
   ```

6. Inspecionar a interface e os cálculos; fazer commit e push pelo GitHub Desktop após revisão.

Esta entrega foi verificada por **21 testes automatizados** e compilação sintática dos arquivos Python. As interações no servidor Streamlit real não foram inspecionadas visualmente nesta execução porque o pacote Streamlit não está instalado no ambiente de teste.

## Configuração do caso: velocidade 35 m/min

No app:

- `1 · SYSTEM INPUTS`: velocidade desejada 35 m/min; demais valores iniciais preservados, conforme a serra-fita de referência.
- `2 · DRIVE CONNECTION`: `Direct` — **hipótese inicial de trabalho**.
- `3 · PROVIDED DRIVE` → `IBR Q catalogue`.
- `IBR Q frame` = `090`, `Ratio i` = `40`, potência = `3 cv` (= 2,2065 kW), motor = `1700 rpm`.
- Selecionar `Starts / hour`, `Load classification` e `Operation [hours/day]` correspondentes ao serviço **real**. Os padrões `<10`, `Moderate shocks`, `2–10` são apenas exemplo conservador para mostrar o recurso; **não foram fornecidos pelo usuário**.

Resultados esperados do transportador com retorno guiado, μ_top=0,35, μ_ret=0,25, massa transportada=276 kg, C=4,15554 m, Dp=260 mm, 4 vias, 7,30 kg/m/via, t_a=3 s e f_d=1,50:

| Grandeza | Valor aproximado |
|---|---:|
| Rotação do eixo requerida | 42,85 rpm |
| Força de projeto | 2651,0 N |
| Torque de projeto | 344,63 N·m |
| Potência de projeto | 1,546 kW |
| Torque base (antes de f_d) | 229,76 N·m |

IBR Q090 — `i=40`, `3 cv`, `n1=1700 rpm`:

| Campo do catálogo | Valor |
|---|---:|
| n2 | 42,5 rpm |
| M2M com 3 cv | 366,8 N·m |
| M2Nom | 403 N·m |
| η | 74% |
| PNom | 3,29 cv |
| FR2 | 4580 N |
| f.s. no catálogo com motor 3 cv | 1,1 |
| Velocidade de transporte com ligação direta | 34,715 m/min |

### Fatores de serviço: três razões distintas

O programa informa separadamente:

1. **f.s. no torque nominal gerado pelo motor:** `M2Nom/M2M` = `403/366,8` ≈ **1,10**. É a definição indicada no glossário do catálogo, p.4.
2. **f.s. relativo à carga-base calculada:** `M2Nom/M_base` = `403/229,76` ≈ **1,75**. É diagnóstico da utilização efetiva, considerando a carga calculada (inclusive a aceleração) antes do fator de projeto.
3. **Margem nominal sobre o torque de projeto:** `M2Nom/M_design` = `403/344,63` ≈ **1,17**.

O fator de projeto `f_d=1,50` já multiplica a demanda no cálculo do transportador. A seleção pelo critério `f.s.` de catálogo e a margem interna do modelo devem ser reconciliadas com o fabricante para evitar margens duplicadas ou insuficientes. Os resultados do programa são uma **pré-seleção**, não uma homologação térmica/dinâmica do conjunto.

Para o regime de exemplo `<10 partidas/h`, `Moderate shocks`, `2–10 h/dia`, a tabela da IBR exige `f.s.≥1,25`; o fator de serviço de referência do conjunto com motor de 3 cv é 1,10. Isso requer análise da condição real de carga e aprovação da IBR. Uma alternativa numericamente viável é **IBR Q110, i=40, motor 3 cv**: torque calculado ≈391,5 N·m e f.s. no motor ≈1,83, mantendo a mesma velocidade nominal. Essa alternativa não constitui recomendação final antes da validação mecânica e comercial.

### Caso com transmissão secundária

Usando `Dp1=170 mm`, `Dp2=202,66 mm`, `η_sec=98%`:

- n_red,req ≈ 51,08 rpm, equivalente a i_red ideal ≈ 33,28 com n_motor=1700 rpm.
- IBR Q090 i40 gera velocidade linear ≈29,12 m/min, **não atende a 35 m/min** com esses diâmetros.
- O catálogo IBR da página 5 prevê, para engrenagem ligada por corrente, `fk=1,25` e fator de ponto de aplicação `p` dependente do posicionamento. Estimativa no eixo do redutor: `FR≈2000 × M2M × fk × p / Dp1(mm)`.
- Para Q090 i40 com motor 3 cv e Dp1=170 mm, `p=1`, a estimativa no torque nominal gerado é aproximadamente **5394 N**, maior que `FR2=4580 N`; exige revisão da solução.
- A calculadora mantém o resultado de carga radial como `REVIEW`, pois a soma vetorial das tensões dos ramos, a pré-tensão e a geometria não foram implementadas completamente. A estimativa IBR é um critério **separado** e deve ter seu ponto de aplicação verificado.

## Rastreamento e ressalvas do catálogo

Fonte exclusiva dos dados tabulados: **`IBR pgs.pdf` fornecido pelo usuário**, páginas impressas **4–5, 9, 13–14**. O código contém uma transcrição parcial e identificada das tabelas: tamanhos **075, 090, 110, 130 e 150**, reduções **30, 40 e 50**. **Não afirmar que o seletor cobre toda a linha IBR Q**. Os dados foram testados especialmente para Q090/i40 e Q110/i40.

Inconsistências na impressão do catálogo:

- **Página 4:** define `f.s. = M2Nom/M2M`, consistente com os fatores tabulados. **Página 9, EQ.2:** inverte essa fração. O aplicativo usa a definição da página 4 e a coerência da tabela.
- **Página 5, potência de movimentação linear:** `F(N) × v(m/s) / 1000` resulta em **kW**, embora a fórmula impressa a rotule como `cv`. O aplicativo calcula em kW e converte usando `1 cv = 0,73549875 kW`.
- Nas tabelas IBR considera-se `n1=1700 rpm`, com motor de 4 polos. A entrada de outra rotação altera a previsão de n2, mas o rendimento e o torque máximo continuam os tabulados e podem requerer validação do fabricante.
- `FR2` vale para a posição de aplicação especificada pelo fabricante (centro da chaveta); o programa não conhece automaticamente a distância real do elemento transmissor.
- As categorias de partidas por hora no catálogo são `<10` e `>10`; **o valor exatamente 10 não aparece explicitamente atribuído**. Consultar o fornecedor nessa fronteira.

## Componentes modificados

- `src/ibr_catalog.py`: tabela IBR parcial, equações do motoredutor, fatores de serviço e força radial simplificada da IBR.
- `app.py`: terceiro modo de fornecimento, seleção, comparação de opções, memória de cálculo IBR e 35 m/min como valor inicial.
- `src/calculations.py`: contém os aprimoramentos do pacote anterior (massas e forças por trecho, conversões). A seleção IBR acrescentada é independente da mecânica de transportador já existente.
- `tests/test_ibr_catalog.py`: verificações do caso Q090, Q110, serviço, velocidade, torque e força radial.
- `tests/test_calculations.py` e `tests/test_app_smoke.py`: regressão das funcionalidades e execução estrutural da nova opção de interface.

## Antes de definir o modelo comercial

Confirmar: (1) ligação direta ou com corrente secundária; (2) horas de operação diárias, partidas/h e choques; (3) se a rotação real do motor será 1700 rpm ou outra; (4) montagem (eixo vazado/maciço) e posicionamento de cargas radiais; (5) características térmicas e de partida.
