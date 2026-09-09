"""
Modelo do Gabarito Oficial
Armazena e gerencia o gabarito correto para comparação.
"""

from typing import Dict, List, Optional
from config import ANSWER_SHEET_CONFIG


class AnswerSheet:
    """Gerencia o gabarito oficial do simulado."""

    def __init__(self):
        self.num_questions = ANSWER_SHEET_CONFIG["num_questions"]
        self.alternatives = ANSWER_SHEET_CONFIG["alternatives"]
        self._gabarito: Dict[int, str] = {}

    def set_answer(self, question: int, answer: str) -> bool:
        """Define a resposta correta para uma questão."""
        if 1 <= question <= self.num_questions and answer.upper() in self.alternatives:
            self._gabarito[question] = answer.upper()
            return True
        return False

    def get_answer(self, question: int) -> Optional[str]:
        """Retorna a resposta correta de uma questão."""
        return self._gabarito.get(question)

    def set_gabarito(self, gabarito: Dict[int, str]) -> bool:
        """Define o gabarito completo de uma vez."""
        for q, a in gabarito.items():
            if not self.set_answer(q, a):
                return False
        return True

    def get_gabarito(self) -> Dict[int, str]:
        """Retorna o gabarito completo."""
        return self._gabarito.copy()

    def is_complete(self) -> bool:
        """Verifica se todas as questões têm gabarito."""
        return len(self._gabarito) == self.num_questions

    def get_missing_questions(self) -> List[int]:
        """Retorna lista de questões sem gabarito."""
        return [q for q in range(1, self.num_questions + 1) if q not in self._gabarito]

    def load_from_list(self, answers: List[str]) -> bool:
        """Carrega gabarito a partir de lista ['A', 'C', 'B', ...]."""
        if len(answers) != self.num_questions:
            return False
        for i, ans in enumerate(answers, 1):
            if not self.set_answer(i, ans):
                return False
        return True

    def to_list(self) -> List[str]:
        """Retorna gabarito como lista."""
        return [self._gabarito.get(i, "") for i in range(1, self.num_questions + 1)]


# Instância global para uso fácil
OFFICIAL_ANSWER_SHEET = AnswerSheet()