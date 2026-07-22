# src/simulator/base.py
# ─────────────────────────────────────────────
# CONCEITO: Herança — todos os simuladores herdam desta classe.
# Isso garante que todos tenham a mesma interface (gerar_leitura, publicar).
# ─────────────────────────────────────────────

import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class SensorBase(ABC):
    """
    Classe-mãe de todos os sensores simulados.

    ANALOGIA: É o "gabarito" de um sensor real. Todo sensor tem:
    - Um equipamento associado
    - Uma função de leitura
    - Um comportamento normal + capacidade de injetar anomalia

    POR QUÊ: ABC (Abstract Base Class) = garante que subclasses implementem
    os métodos obrigatórios. Se esquecer, o Python avisa na hora.
    """

    def __init__(
        self,
        equipamento_id: str,
        seed: int = 42,
        taxa_falha: float = 0.0,  # 0.0 = sem falhas, 1.0 = sempre falha
    ):
        self.equipamento_id = equipamento_id
        self.taxa_falha = taxa_falha
        self.anomalia_ativa = False
        self.tipo_anomalia: Optional[str] = None

        # POR QUÊ seed fixa: resultados REPRODUZÍVEIS.
        # Mesmo seed = mesma sequência de "aleatórios".
        # Essencial para testes e debug.
        self.rng = random.Random(seed)

        # Contador de leituras (útil para tendências)
        self.contador_leituras = 0

    @abstractmethod
    def gerar_leitura_normal(self) -> Dict[str, Any]:
        """
        Gera uma leitura em condições NORMAIS de operação.
        CADA SUBCLASSE DEVE IMPLEMENTAR.

        Returns:
            Dict com os valores dos sensores específicos do equipamento.
        """
        ...

    def gerar_leitura(self) -> Dict[str, Any]:
        """
        Gera uma leitura — normal OU com anomalia injetada.

        Fluxo:
        1. Decide se esta leitura terá anomalia (baseado na taxa_falha)
        2. Se sim, gera leitura anômala
        3. Se não, gera leitura normal + ruído

        POR QUÊ: Este método é comum a TODOS os sensores.
        As subclasses só implementam o comportamento específico.
        """
        self.contador_leituras += 1

        # Decide se injeta anomalia
        if self.anomalia_ativa or self.rng.random() < self.taxa_falha:
            leitura = self.injetar_anomalia()
        else:
            leitura = self.gerar_leitura_normal()
            leitura = self._adicionar_ruido(leitura)

        # Metadados comuns a todas as leituras
        leitura["equipamento_id"] = self.equipamento_id
        leitura["timestamp"] = datetime.now(timezone.utc).isoformat()
        leitura["anomalia_detectada"] = self.anomalia_ativa
        leitura["tipo_anomalia"] = self.tipo_anomalia

        return leitura

    def _adicionar_ruido(self, leitura: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adiciona ruído gaussiano (normal) aos valores.

        POR QUÊ: Sensores reais NUNCA têm leituras perfeitamente estáveis.
        Sem ruído, o dado parece "artificial demais".

        ANALOGIA: É a "tolerância" de um instrumento de medição.
        Um paquímetro digital mostra 10.00mm, mas o real é 10.003mm.
        """
        for chave, valor in leitura.items():
            if isinstance(valor, (int, float)):
                # Ruído de 0.5% do valor, com distribuição normal
                ruido = self.rng.gauss(0, abs(valor) * 0.005)
                leitura[chave] = round(valor + ruido, 4)
        return leitura

    @abstractmethod
    def injetar_anomalia(self) -> Dict[str, Any]:
        """
        Gera uma leitura ANÔMALA.
        CADA SUBCLASSE DEFINE SEUS TIPOS DE ANOMALIA.
        """
        ...

    def ativar_anomalia(self, tipo: str):
        """
        Ativa manualmente uma anomalia específica.
        Útil para testes e demonstrações.
        """
        self.anomalia_ativa = True
        self.tipo_anomalia = tipo

    def desativar_anomalia(self):
        """Retorna ao comportamento normal."""
        self.anomalia_ativa = False
        self.tipo_anomalia = None
