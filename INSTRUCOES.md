# Chain Conveyor Calculator — atualização da interface

**Entrega:** arquivos completos, sem necessidade de Python instalado no Windows.

## Substituição pelo GitHub Desktop

1. Baixe e extraia o ZIP desta entrega.
2. Abra a pasta local do repositório no Windows:
   `C:\Users\Douglas\Documents\GitHub\chain-conveyor-calculator`
3. Copie o conteúdo extraído **para dentro da pasta do repositório**, substituindo os arquivos de mesmo nome.
4. **Não apague** as pastas `assets`, `.git`, nem os demais arquivos existentes. Os esquemas e imagens permanecem originais.
5. No GitHub Desktop, confirme as alterações em `app.py`, `src/` e `tests/`.
6. Faça commit e **Push origin**. O Streamlit Community Cloud normalmente fará o redeploy do `main`.
7. Abra `https://chain-conveyor-calculator.streamlit.app/` para conferir o resultado. Se precisar, use o menu *Manage app → Reboot*.

Não é necessário executar nenhum script no computador: os arquivos já estão editados.

## Alterações

- `C` padrão: **4,5 m**; `Dp` padrão: **202,66 mm**; velocidade padrão: **35 m/min**.
- Acima: **carga transportada → massa das correntes superiores → massa apoiada → μ_top → F_top**.
- Abaixo: **massa das correntes no retorno → μ_ret → F_ret**, sendo os dois últimos campos mostrados apenas no retorno guiado; também são exibidas as massas nos arcos e total de correntes.
- A massa das correntes superiores é somada à massa transportada antes do cálculo de atrito. A força normal do modelo é `massa apoiada × 9,81 × cos(α)`, em newtons.
- Apenas **Motoredutor completo** e **Redutor e motor separados** na seção 3; não há opção *Catálogo IBR Q*.
- O formulário genérico de motoredutor completo abre com parâmetros de exemplo IBR Q090, redução 40, motor 3 cv. São dados editáveis, não uma seleção validada.
- Removidos o bloco 4 de comparação, avisos de fator de serviço, alternativas automáticas IBR, glossário, metodologia e aviso geral de pontuação decimal.
- Redução da largura das imagens do acionamento e da calculadora auxiliar para aproximadamente 50%, mantendo os arquivos originais.
- A calculadora auxiliar de massa permanece funcional, em seção recolhível com título mais curto.
- A conversão editável em ambos os sentidos entre kW e cv foi preservada.

## Arquivos incluídos

- `app.py` — interface Streamlit completa, revista.
- `src/calculations.py` — motor de equações independente da interface.
- `src/localization.py` — entrada e saída numérica em português brasileiro.
- `src/__init__.py` — pacote Python.
- `requirements.txt` — dependências do Streamlit Cloud.
- `tests/test_app_smoke.py`, `tests/test_calculations.py`, `tests/test_streamlit_runtime.py` — testes.

O módulo anterior `src/ibr_catalog.py` pode permanecer no repositório: não é mais chamado pela interface, mas pode ser reutilizado futuramente.

## Verificação executada

- Compilação sintática dos arquivos Python: aprovada.
- `python -m unittest discover -s tests -v`: **14 testes aprovados; 2 testes de interface real ignorados**, porque Streamlit não está instalado no ambiente usado para esta preparação.
- O ambiente do Streamlit Cloud e o layout visual final ainda **não foram validados em execução real**.

## Atenção de dimensionamento

Com `Dp = 202,66 mm` e `v = 35 m/min`, a rotação necessária no eixo transportador é aproximadamente **54,97 rpm**. Um IBR Q090 com i=40 e 1.700 rpm na entrada fornece aproximadamente **42,5 rpm**. Portanto, nessa condição de acoplamento direto, o conjunto não alcança 35 m/min. O formulário do motorredutor apenas recebe dados de catálogo; a avaliação da seleção foi retirada junto com o bloco 4, conforme solicitado.
