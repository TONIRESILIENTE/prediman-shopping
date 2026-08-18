# src/services/pops_service.py
# ─────────────────────────────────────────────
# CONCEITO: Base de conhecimento dos POPs.
#
# Cada POP é um procedimento completo que o técnico
# recebe junto com a OS. Contém:
# - Passo a passo técnico
# - EPIs obrigatórios (segurança)
# - Ferramentas necessárias
# - Tempo estimado
# - Riscos envolvidos
#
# Em produção, isso viria do banco de dados e seria
# editável pelo gestor via painel admin.
# ─────────────────────────────────────────────

from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class POP:
    """Procedimento Operacional Padrão."""
    codigo: str
    titulo: str
    equipamento_tipo: str
    tempo_estimado_minutos: int
    epis: list = field(default_factory=list)
    ferramentas: list = field(default_factory=list)
    passos: list = field(default_factory=list)
    riscos: list = field(default_factory=list)
    observacoes: str = ""
    animacao_url: str = ""


# ─── BASE DE POPs ────────────────────────────
# POR QUÊ: Cada código POP segue o padrão:
# POP-{TIPO_EQUIPAMENTO}-{NUMERO}
# Ex: POP-CHL-001 = Chiller, procedimento 001

POPS: Dict[str, POP] = {

    # ═══════════════════════════════════════════
    # CHILLER
    # ═══════════════════════════════════════════

    "POP-CHL-001": POP(
        codigo="POP-CHL-001",
        titulo="Verificação de Compressor com Vibração Anômala",
        equipamento_tipo="chiller",
        tempo_estimado_minutos=45,
        epis=[
            "Luva de proteção mecânica",
            "Óculos de segurança",
            "Protetor auricular (ruído > 85dB)",
            "Capacete",
            "Calçado de segurança",
        ],
        ferramentas=[
            "Analisador de vibração triaxial",
            "Multímetro digital",
            "Chave Allen 8mm",
            "Termômetro infravermelho",
            "Estetoscópio mecânico",
        ],
        passos=[
            "1. DESLIGAR o chiller no painel principal de comando",
            "2. BLOQUEAR disjuntor principal (procedimento Lockout/Tagout — NR-10)",
            "3. Aguardar 5 minutos para resfriamento das superfícies",
            "4. Remover a tampa de proteção do compressor",
            "5. Medir vibração nos 3 eixos (horizontal, vertical, axial) com analisador",
            "6. Comparar leituras com baseline do equipamento (normal: 2-4 mm/s)",
            "7. Se vibração > 7.0 mm/s: PROGRAMAR substituição do rolamento",
            "8. Verificar alinhamento entre motor e compressor",
            "9. Inspecionar visualmente: vazamentos de óleo, folgas, corrosão",
            "10. Registrar todas as leituras na OS e no histórico do equipamento",
            "11. Reinstalar tampa de proteção",
            "12. Remover bloqueio, religar e monitorar partida por 10 minutos",
        ],
        riscos=[
            "Choque elétrico (440V — circuito de força)",
            "Superfície quente (tubulação de gás refrigerante até 80°C)",
            "Ruído elevado durante operação",
            "Peças móveis (ventilador do condensador)",
        ],
        observacoes="Se vibração entre 5.0 e 7.0 mm/s: monitorar tendência por 48h antes de programar troca.",
        animacao_url="/pwa/animations/chiller-vibracao.json",
    ),

    "POP-CHL-002": POP(
        codigo="POP-CHL-002",
        titulo="Avaliação de Baixa Eficiência Térmica (ΔT Reduzido)",
        equipamento_tipo="chiller",
        tempo_estimado_minutos=60,
        epis=[
            "Luva de proteção mecânica",
            "Óculos de segurança",
            "Luva térmica (superfícies quentes)",
            "Capacete",
        ],
        ferramentas=[
            "Manifold de pressão (gás refrigerante)",
            "Termômetro de contato",
            "Bomba de vácuo",
            "Detector de vazamento eletrônico",
            "Escova de limpeza para trocador de calor",
        ],
        passos=[
            "1. DESLIGAR o chiller e bloquear disjuntor (Lockout/Tagout)",
            "2. Medir temperaturas de entrada e saída de água com termômetro calibrado",
            "3. Calcular ΔT = T_entrada - T_saída (normal: 4-6°C)",
            "4. Se ΔT < 3°C: conectar manifold e verificar pressão do gás refrigerante",
            "5. Comparar pressão com tabela do fabricante para temperatura ambiente",
            "6. Se pressão baixa: realizar teste de vazamento com detector eletrônico",
            "7. Inspecionar trocadores de calor (possível incrustação)",
            "8. Limpar trocadores se necessário (escova + solução recomendada)",
            "9. Se vazamento confirmado: isolar trecho, recuperar gás, soldar, vácuo, recarregar",
            "10. Registrar pressões, temperaturas e ações na OS",
            "11. Remover bloqueio, religar e verificar ΔT após 20 min de operação",
        ],
        riscos=[
            "Contato com gás refrigerante (risco de queimadura por frio)",
            "Alta pressão no circuito (até 350 PSI)",
            "Choque elétrico",
        ],
        observacoes="Certificação NR-13 (vasos de pressão) exigida para intervenção no circuito de gás.",
        animacao_url="/pwa/animations/chiller-vibracao.json",

    ),

    "POP-CHL-003": POP(
        codigo="POP-CHL-003",
        titulo="Verificação de Sobrecarga Elétrica no Compressor",
        equipamento_tipo="chiller",
        tempo_estimado_minutos=30,
        epis=[
            "Luva isolante classe 0 (1000V)",
            "Óculos de segurança",
            "Capacete",
            "Calçado de segurança",
        ],
        ferramentas=[
            "Alicate amperímetro (True RMS)",
            "Multímetro com escala de capacitância",
            "Termômetro infravermelho",
            "Chave de fenda isolada",
        ],
        passos=[
            "1. NÃO desligar o equipamento inicialmente — medir com carga",
            "2. Medir corrente nas 3 fases do compressor com alicate amperímetro",
            "3. Comparar com valor nominal da placa do motor",
            "4. Se > 80A: verificar balanceamento entre fases (diferença máx 5%)",
            "5. Medir tensão entre fases (380V ± 10%)",
            "6. Verificar temperatura dos bornes com termômetro (máx 70°C)",
            "7. Inspecionar contatos do contator (possível desgaste/carvão)",
            "8. Medir capacitores de partida e permanente (se aplicável)",
            "9. Verificar carga térmica: todas as válvulas de água gelada abertas?",
            "10. Registrar todas as medições na OS",
            "11. Se necessário, DESLIGAR e programar substituição de componentes",
        ],
        riscos=[
            "Choque elétrico (440V — medição com equipamento energizado)",
            "Arco elétrico (bornes com mau contato)",
            "Queimadura (superfícies quentes)",
        ],
        observacoes="Medição com equipamento energizado: obrigatório uso de luva isolante + acompanhante habilitado (NR-10).",
        animacao_url="/pwa/animations/chiller-vibracao.json",
    ),

    # ═══════════════════════════════════════════
    # SUBESTAÇÃO
    # ═══════════════════════════════════════════

    "POP-SUB-001": POP(
        codigo="POP-SUB-001",
        titulo="Correção de Fator de Potência — Banco de Capacitores",
        equipamento_tipo="subestacao",
        tempo_estimado_minutos=40,
        epis=[
            "Luva isolante classe 2 (17.5kV)",
            "Capacete classe B",
            "Óculos de proteção contra arco elétrico",
            "Calçado de segurança",
        ],
        ferramentas=[
            "Analisador de qualidade de energia",
            "Multímetro True RMS CAT IV",
            "Chave de fenda isolada",
            "Alicate amperímetro",
        ],
        passos=[
            "1. Verificar se o banco de capacitores está em operação automática",
            "2. Medir fator de potência com analisador de qualidade de energia",
            "3. Se FP < 0.92: verificar quais estágios do banco estão acionados",
            "4. Inspecionar visualmente: capacitores estufados, vazamento de óleo",
            "5. Medir corrente em cada capacitor com alicate amperímetro",
            "6. Comparar corrente medida com nominal (desvio > 10% = capacitor degradado)",
            "7. Verificar fusíveis de proteção de cada estágio",
            "8. Substituir capacitores com defeito (DESLIGAR banco antes — esperar 5 min para descarga)",
            "9. Verificar configuração do controlador automático (ajuste de sensibilidade)",
            "10. Medir FP novamente após correção — deve estar entre 0.92 e 0.98",
        ],
        riscos=[
            "Risco elétrico grave (subestação — 380V/13.8kV)",
            "Explosão de capacitor (curto-circuito interno)",
            "Arco elétrico",
        ],
        observacoes="Serviço em subestação: obrigatório dupla de trabalho (NR-10). Capacitores mantêm carga após desligamento — aguardar descarga.",
        animacao_url="/pwa/animations/subestacao-eletrica.json",
    ),

    "POP-SUB-002": POP(
        codigo="POP-SUB-002",
        titulo="Balanceamento de Cargas entre Fases",
        equipamento_tipo="subestacao",
        tempo_estimado_minutos=60,
        epis=[
            "Luva isolante classe 2",
            "Capacete classe B",
            "Protetor facial contra arco elétrico",
            "Calçado de segurança",
        ],
        ferramentas=[
            "Analisador de qualidade de energia trifásico",
            "Alicate amperímetro True RMS",
            "Chave de fenda isolada",
            "Etiquetas para identificação de circuitos",
        ],
        passos=[
            "1. Medir corrente nas 3 fases do QGBT com analisador",
            "2. Registrar leituras: Fase R, S, T",
            "3. Calcular desbalanceamento: (I_max - I_min) / I_media × 100%",
            "4. Se > 10%: identificar circuitos monofásicos que estão sobrecarregando uma fase",
            "5. Mapear distribuição de cargas por fase (usar etiquetas)",
            "6. Redistribuir circuitos monofásicos entre fases para equilibrar",
            "7. ATENÇÃO: desligar circuitos antes de realocar (choque elétrico)",
            "8. Após redistribuição, medir novamente as 3 fases",
            "9. Repetir ajustes até desbalanceamento < 5%",
            "10. Atualizar diagrama unifilar com nova distribuição",
        ],
        riscos=[
            "Risco elétrico grave (trabalho em QGBT energizado)",
            "Queda parcial de energia durante manobra",
            "Arco elétrico",
        ],
        observacoes="Coordenar com operação do shopping: desligamento de circuitos pode afetar lojas. Programar em horário de menor movimento.",
        animacao_url="/pwa/animations/subestacao-eletrica.json",
    ),

    "POP-SUB-003": POP(
        codigo="POP-SUB-003",
        titulo="Verificação de Oscilação de Tensão",
        equipamento_tipo="subestacao",
        tempo_estimado_minutos=30,
        epis=[
            "Luva isolante classe 1",
            "Óculos de segurança",
            "Capacete",
        ],
        ferramentas=[
            "Multímetro True RMS CAT IV",
            "Analisador de qualidade de energia",
            "Chave de fenda isolada",
        ],
        passos=[
            "1. Conectar analisador de qualidade de energia no ponto de acoplamento",
            "2. Configurar para registrar tensão por 15 minutos (mínimo)",
            "3. Verificar se oscilações coincidem com partida de grandes cargas (chillers, bombas)",
            "4. Medir tensão em vazio e com carga máxima",
            "5. Inspecionar conexões do transformador (possível mau contato)",
            "6. Verificar comutador de tap do transformador (se ajustável)",
            "7. Se tensão persistentemente fora da faixa (±10%): acionar concessionária",
            "8. Registrar gráfico de tendência na OS",
        ],
        riscos=[
            "Risco elétrico (medição em equipamento energizado)",
            "Queda de tensão pode danificar equipamentos eletrônicos",
        ],
        observacoes="Oscilações podem ser da rede da concessionária — registrar horários para acionamento formal.",
        animacao_url="/pwa/animations/subestacao-eletrica.json",
    ),

    "POP-SUB-004": POP(
        codigo="POP-SUB-004",
        titulo="Sobreaquecimento de Barramentos",
        equipamento_tipo="subestacao",
        tempo_estimado_minutos=25,
        epis=[
            "Luva isolante classe 2",
            "Protetor facial contra arco",
            "Capacete classe B",
        ],
        ferramentas=[
            "Termômetro infravermelho (até 200°C)",
            "Câmera termográfica (opcional — ideal)",
            "Chave torqueada para reaperto de conexões",
        ],
        passos=[
            "1. Medir temperatura de TODOS os barramentos e conexões com termômetro",
            "2. Identificar pontos com temperatura > 70°C",
            "3. Comparar temperatura entre fases no mesmo ponto (diferença > 10°C = anomalia)",
            "4. Verificar torque dos parafusos de conexão (conforme especificação do fabricante)",
            "5. Inspecionar visualmente: oxidação, descoloração, carbonização",
            "6. Limpar contatos oxidados com escova adequada e aplicar pasta condutora",
            "7. Reapertar conexões frouxas com chave torqueada",
            "8. Verificar ventilação do cubículo (grelhas obstruídas? ventilador funcionando?)",
            "9. Medir novamente após 15 min de operação para confirmar redução",
            "10. Se temperatura não baixar: programar desligamento para inspeção detalhada",
        ],
        riscos=[
            "Risco elétrico extremo (barramentos energizados)",
            "Arco elétrico (conexão frouxa pode abrir arco)",
            "Queimadura por contato",
        ],
        observacoes="Barramentos acima de 70°C: risco de incêndio por ignição de isolantes próximos. Ação IMEDIATA.",
        animacao_url="/pwa/animations/subestacao-eletrica.json",
    ),

    # ═══════════════════════════════════════════
    # BOMBA DE RECALQUE
    # ═══════════════════════════════════════════

    "POP-BOM-001": POP(
        codigo="POP-BOM-001",
        titulo="Diagnóstico e Correção de Cavitação",
        equipamento_tipo="bomba",
        tempo_estimado_minutos=50,
        epis=[
            "Luva de proteção mecânica",
            "Óculos de segurança",
            "Protetor auricular",
            "Calçado impermeável (área de poço)",
        ],
        ferramentas=[
            "Analisador de vibração",
            "Alicate amperímetro",
            "Chave de grifa 24\"",
            "Lanterna à prova d'água",
            "Trena (medir nível do poço)",
        ],
        passos=[
            "1. Confirmar assinatura de cavitação: vibração alta + corrente baixa",
            "2. Medir nível real do poço com trena (comparar com sensor)",
            "3. Se nível OK: verificar folga do rotor (desgaste aumenta cavitação)",
            "4. Inspecionar tubulação de sucção: vazamentos de ar? válvula de pé funcionando?",
            "5. Verificar se filtro de sucção está obstruído (limpar se necessário)",
            "6. Verificar diâmetro da tubulação de sucção (subdimensionamento causa cavitação)",
            "7. Se necessário: DESLIGAR, remover bomba, inspecionar rotor",
            "8. Substituir rotor se apresentar pitting (marcas de cavitação)",
            "9. Remontar, religar e verificar vibração/corrente",
            "10. Registrar causas e ações na OS",
        ],
        riscos=[
            "Espaço confinado (poço de recalque) — NR-33",
            "Afogamento (trabalho próximo à água)",
            "Choque elétrico (bomba submersa)",
            "Atmosfera potencialmente tóxica (gases do esgoto)",
        ],
        observacoes="Poço de recalque é espaço confinado: obrigatório uso de medidor de gases + dupla de trabalho + resgate disponível (NR-33).",
        animacao_url="/pwa/animations/bomba-agua.json",
    ),

    "POP-BOM-002": POP(
        codigo="POP-BOM-002",
        titulo="Verificação de Obstrução na Tubulação",
        equipamento_tipo="bomba",
        tempo_estimado_minutos=40,
        epis=[
            "Luva de proteção mecânica",
            "Óculos de segurança",
            "Calçado impermeável",
        ],
        ferramentas=[
            "Manômetro (0-10 bar)",
            "Alicate amperímetro",
            "Chave de grifa",
            "Câmera de inspeção (borehole) — se disponível",
        ],
        passos=[
            "1. Confirmar assinatura: corrente alta + vibração normal",
            "2. Instalar manômetro na saída da bomba e medir pressão",
            "3. Comparar com curva característica da bomba (catálogo do fabricante)",
            "4. Se pressão anormalmente alta: obstrução a jusante (tubulação, válvula, filtro)",
            "5. Verificar válvulas de bloqueio: alguma parcialmente fechada?",
            "6. Inspecionar filtro Y (se existir) — limpar",
            "7. Se possível, inserir câmera de inspeção na tubulação",
            "8. Identificar ponto de obstrução (acúmulo de detritos, incrustação)",
            "9. Remover obstrução: limpeza química ou mecânica",
            "10. Medir pressão e corrente após correção",
        ],
        riscos=[
            "Jato d'água sob pressão (desconexão acidental de manômetro)",
            "Espaço confinado (dependendo da localização da tubulação)",
        ],
        observacoes="Obstruções recorrentes: avaliar instalação de filtro Y ou grade na entrada do poço.",
        animacao_url="/pwa/animations/bomba-agua.json",
    ),

    "POP-BOM-003": POP(
        codigo="POP-BOM-003",
        titulo="CRÍTICO: Poço de Recalque Seco",
        equipamento_tipo="bomba",
        tempo_estimado_minutos=30,
        epis=[
            "Luva isolante (risco elétrico)",
            "Óculos de segurança",
            "Capacete",
            "Calçado impermeável",
        ],
        ferramentas=[
            "Trena ou medidor de nível",
            "Multímetro",
            "Lanterna",
        ],
        passos=[
            "1. CONFIRMAR leitura do sensor de nível",
            "2. Se poço realmente seco: DESLIGAR bomba IMEDIATAMENTE (risco de queima)",
            "3. Bloquear partida automática (desligar controle automático)",
            "4. Investigar causa: falta d'água na rede? rompimento de tubulação de alimentação?",
            "5. Verificar se há vazamento visível na tubulação de entrada do poço",
            "6. Contatar concessionária de água se falta de abastecimento",
            "7. Aguardar nível normalizar antes de religar",
            "8. Verificar funcionamento da boia de nível (testar com balde d'água)",
            "9. Substituir sensor de nível se defeituoso",
            "10. Manter bomba desligada até garantia de abastecimento normalizado",
        ],
        riscos=[
            "Queima da bomba (operação a seco = superaquecimento em segundos)",
            "Choque elétrico (bomba danificada pode ter fuga para água)",
            "Alagamento se bomba ficar desligada e poço voltar a encher (verificar extravasor)",
        ],
        observacoes="Bomba operando a seco queima em menos de 2 minutos. Tempo de resposta CRÍTICO. Acionar supervisão imediata.",
        animacao_url="/pwa/animations/bomba-agua.json",
    ),

    "POP-BOM-004": POP(
        codigo="POP-BOM-004",
        titulo="Verificação de Vibração Excessiva em Bomba",
        equipamento_tipo="bomba",
        tempo_estimado_minutos=35,
        epis=[
            "Luva de proteção mecânica",
            "Óculos de segurança",
            "Protetor auricular",
        ],
        ferramentas=[
            "Analisador de vibração",
            "Chave Allen (para base)",
            "Relógio comparador (alinhamento)",
            "Chave de grifa",
        ],
        passos=[
            "1. Medir vibração nos 3 eixos (horizontal, vertical, axial)",
            "2. Identificar frequência predominante (desbalanceamento = 1× rotação; desalinhamento = 2×)",
            "3. Verificar aperto dos parafusos da base (chave Allen)",
            "4. Medir alinhamento motor-bomba com relógio comparador",
            "5. Se desalinhado: realinhar conforme tolerância do fabricante",
            "6. Inspecionar base de concreto: trincas? nivelamento?",
            "7. Verificar se há tubulação apoiada na bomba (força externa)",
            "8. Após correções, medir vibração novamente",
            "9. Registrar valores antes/depois na OS",
        ],
        riscos=[
            "Peças rotativas (eixo exposto)",
            "Ruído elevado",
        ],
        observacoes="Vibração persistente após correções: avaliar balanceamento dinâmico do rotor em oficina especializada.",
        animacao_url="/pwa/animations/bomba-agua.json",
    ),

    # ═══════════════════════════════════════════
    # ILUMINAÇÃO
    # ═══════════════════════════════════════════

    "POP-ILU-001": POP(
        codigo="POP-ILU-001",
        titulo="Verificação de Timer/Fotocélula — Luzes Fora do Horário",
        equipamento_tipo="iluminacao",
        tempo_estimado_minutos=20,
        epis=[
            "Luva isolante (trabalho em QDL)",
            "Óculos de segurança",
            "Calçado de segurança",
        ],
        ferramentas=[
            "Multímetro",
            "Chave de fenda isolada",
            "Lanterna",
        ],
        passos=[
            "1. Confirmar que luzes estão acesas fora do horário programado",
            "2. Ir ao QDL correspondente e identificar o contator do circuito",
            "3. Verificar se o contator está acionado (barulho + indicação visual)",
            "4. Testar timer: forçar horário de desligamento manualmente",
            "5. Se timer não desliga: medir tensão na bobina do contator",
            "6. Se tensão presente com timer em 'off': timer defeituoso → substituir",
            "7. Se fotocélula: cobrir sensor e verificar se contator desliga",
            "8. Fotocélula não responde: limpar lente, testar com luz/lanterna",
            "9. Substituir timer ou fotocélula conforme diagnóstico",
            "10. Programar horários corretos no novo timer",
        ],
        riscos=[
            "Choque elétrico (QDL energizado — 220V/380V)",
            "Queda de iluminação durante teste (trabalhar com lanterna)",
        ],
        observacoes="Timer mecânico (analógico): verificar se disco não está travado. Timer digital: verificar bateria interna de memória.",
        animacao_url="/pwa/animations/iluminacao-lampada.json",
    ),

    "POP-ILU-002": POP(
        codigo="POP-ILU-002",
        titulo="Substituição de Lâmpadas Queimadas",
        equipamento_tipo="iluminacao",
        tempo_estimado_minutos=30,
        epis=[
            "Luva isolante",
            "Óculos de segurança",
            "Capacete (trabalho em altura se for teto alto)",
            "Cinto de segurança (altura > 2m — NR-35)",
        ],
        ferramentas=[
            "Multímetro",
            "Escada isolada",
            "Lâmpadas de reposição (LED 50W)",
            "Chave de fenda",
        ],
        passos=[
            "1. Identificar circuito com corrente baixa no dashboard",
            "2. Ir ao local e identificar visualmente lâmpadas apagadas",
            "3. DESLIGAR circuito no QDL (não confiar apenas no interruptor)",
            "4. Bloquear disjuntor (Lockout/Tagout)",
            "5. Remover lâmpadas queimadas",
            "6. Verificar soquete: oxidação? mau contato? (limpar se necessário)",
            "7. Instalar lâmpadas novas (mesma potência e temperatura de cor)",
            "8. Remover bloqueio e religar circuito",
            "9. Verificar se todas acenderam",
            "10. Atualizar registro de lâmpadas substituídas na OS",
        ],
        riscos=[
            "Choque elétrico (soquete pode estar energizado mesmo com interruptor desligado)",
            "Queda de altura (escada/teto)",
            "Queimadura (lâmpada recém-apagada quente)",
        ],
        observacoes="Se > 20% das lâmpadas queimadas simultaneamente: verificar sobretensão no circuito (possível problema no neutro).",
        animacao_url="/pwa/animations/iluminacao-lampada.json"
    ),

    "POP-ILU-003": POP(
        codigo="POP-ILU-003",
        titulo="Avaliação de Degradação de Lâmpadas — Eficiência Luminosa",
        equipamento_tipo="iluminacao",
        tempo_estimado_minutos=25,
        epis=[
            "Luva isolante",
            "Óculos de segurança",
        ],
        ferramentas=[
            "Luxímetro digital",
            "Alicate amperímetro",
            "Calculadora",
        ],
        passos=[
            "1. Confirmar no dashboard: corrente alta com iluminação normal",
            "2. Medir iluminância (lux) em 5 pontos representativos do ambiente",
            "3. Calcular média de iluminância atual",
            "4. Medir corrente total do circuito com alicate",
            "5. Calcular eficiência: lux médio / corrente total",
            "6. Comparar com baseline de quando as lâmpadas eram novas",
            "7. Se eficiência caiu > 20%: lâmpadas degradadas",
            "8. Verificar idade do parque de lâmpadas (data da última troca)",
            "9. Calcular payback da substituição: economia kWh × tarifa vs custo novas lâmpadas",
            "10. Emitir recomendação na OS: 'substituir' ou 'monitorar por mais X meses'",
        ],
        riscos=[
            "Choque elétrico (medição em circuito energizado)",
            "Trabalho em altura (dependendo do ponto de medição)",
        ],
        observacoes="Lâmpadas LED degradam gradualmente (diferente das fluorescentes que queimam). Vida útil típica: 25.000-50.000h. Verificar data de instalação.",
        animacao_url="/pwa/animations/iluminacao-lampada.json",
    ),
}


def buscar_pop(codigo: str) -> Optional[POP]:
    """
    Busca um POP pelo código.

    Args:
        codigo: código do POP (ex: 'POP-CHL-001')

    Returns:
        POP completo ou None se não encontrado
    """
    return POPS.get(codigo.upper())


def listar_pops(equipamento_tipo: Optional[str] = None) -> list[POP]:
    """
    Lista POPs, opcionalmente filtrados por tipo de equipamento.

    Args:
        equipamento_tipo: filtrar por chiller, subestacao, bomba, iluminacao

    Returns:
        Lista de POPs
    """
    if equipamento_tipo:
        return [pop for pop in POPS.values() if pop.equipamento_tipo == equipamento_tipo]
    return list(POPS.values())


def total_pops() -> int:
    """Retorna o total de POPs cadastrados."""
    return len(POPS)
