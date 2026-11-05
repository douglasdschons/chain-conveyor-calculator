# Calculadora de transportadores de correntes — versão 5

## Como atualizar sem Python no Windows

1. Baixe o **app.py** desta versão e substitua o `app.py` da raiz do repositório local `chain-conveyor-calculator` usando o Explorador de Arquivos.
2. Preserve a pasta `assets/` com as imagens. Preserve também `src/` e `requirements.txt` existentes. O ZIP contém cópias compatíveis de `src/calculations.py` e `src/localization.py` caso sejam necessárias.
3. Abra o **GitHub Desktop**, confira que `app.py` aparece alterado, faça **Commit to main** e **Push origin**.
4. Abra o aplicativo publicado no Streamlit Cloud e atualize a página.

O código **não foi publicado automaticamente** neste trabalho. Não há necessidade de instalar Python no computador, porque o Streamlit Cloud executa o servidor.

## Nova seção 4

- **Requerido pelo sistema:** força total, força por via, torque, potência e rotação sem fator adicional.
- **Fator de serviço (FS) da aplicação:** campo editável, padrão **1,00**. O usuário pode selecionar 1,20, 1,50 etc.
- **Requerido com FS:** forças, torque e potência multiplicados **uma vez** pelo FS; a rotação e a velocidade permanecem inalteradas.
- **Comparação:** Requerido com FS × Disponível, com relação `R = disponível / requerido corrigido`, margem `(R - 1) × 100%` e situação.
- O fator de serviço do catálogo do fabricante é apresentado separadamente e **não** multiplica novamente a demanda.

## Correção da redução do redutor

No modo **Motoredutor completo**, selecione **Catálogo IBR Q090** (seleção interna, sem criar terceiro tipo de acionamento). O campo `Redução i (1:i)` permite escolher 1:30, 1:40 ou 1:50. Alterar a redução atualiza automaticamente a rotação, o torque, a potência e a velocidade de saída exibidos na comparação.

Os valores de referência da tabela IBR Q090, página impressa 14, usam motor de 1.700 rpm:

| Relação | PMot tabela | n₂ tabela | M2M tabela | M2Nom | η | FR2 |
|---|---:|---:|---:|---:|---:|---:|
| 1:30 | 4 cv | 56,7 rpm | 396,5 N·m | 418 N·m | 80% | 4.100 N |
| 1:40 | 3 cv | 42,5 rpm | 366,8 N·m | 403 N·m | 74% | 4.580 N |
| 1:50 | 2 cv | 34,0 rpm | 297,4 N·m | 360 N·m | 72% | 4.900 N |

Para um motor com potência diferente da linha, M2M é estimado por proporcionalidade mantendo η constante. Não é confirmação comercial ou térmica. Exceder o PMot indicado gera aviso.

Se o fabricante/modelo não corresponder ao Q090, utilize **Estimativa por rendimento** ou **Saída informada**; neste último caso a rotação e o torque continuam sendo dados manuais, com aviso de incoerência quando não seguem a redução informada.

## Relatório para impressão

Na seção 4, clique em **Gerar relatório para impressão**. Será gerado um arquivo HTML com as entradas, demanda base, FS, demanda corrigida, dados do acionamento, relação de capacidade e notas das equações. Abra o arquivo no navegador e escolha **Imprimir / Salvar como PDF**.

## Referência numérica para conferir

Com C = 4,50 m, Dp = 202,66 mm, quatro vias, q = 7,30 kg/m, massa transportada = 276 kg, μ superior = μ retorno = 0,25, retorno guiado, 35 m/min, 3 s de aceleração, inclinação 0° e F adicional = 0 N:

- Massa superior: **131,40 kg**; massa total das correntes: **281,39 kg**.
- F superior: **999,15 N**; F retorno: **322,26 N**; F aceleração: **108,38 N**.
- Força base: **1.429,79 N**; torque base: **144,88 N·m**; potência base: **0,834 kW**; rotação requerida: **54,97 rpm**.
- Com FS = 1,50, força corrigida = **2.144,68 N**, torque corrigido = **217,32 N·m**, potência corrigida = **1,251 kW**.
- Q090 i40 com motor 3 cv: **42,50 rpm**, **366,8 N·m**, **27,06 m/min**.
- Q090 i30 com motor 3 cv (estimativa): **56,67 rpm**, **297,38 N·m**, **36,08 m/min**.

## Testes

- Python compilação de sintaxe: **passou**.
- **16 testes automatizados** de cálculo e simulação de fluxos do aplicativo: **passaram**.
- Os testes não substituem a renderização do Streamlit real nem a verificação no Streamlit Cloud, que ainda devem ser conferidas após o push.

## Limitações de engenharia

Esta seleção é preliminar. A massa dos arcos é considerada na aceleração. A inércia rotacional de rodas e componentes, impactos reais, capacidade térmica do redutor e cargas radiais de transmissão secundária exigem verificações separadas. O fator da aplicação não equivale ao fator de serviço de catálogo nem à resistência à ruptura da corrente.
