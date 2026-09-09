"""
Módulo de Correção - Compara respostas detectadas com gabarito oficial.
"""

from typing import Dict, List, Tuple
from answer_sheet import OFFICIAL_ANSWER_SHEET, AnswerSheet


class Corrector:
    """Compara respostas detectadas com o gabarito oficial."""

    def __init__(self, answer_sheet: AnswerSheet = None):
        self.answer_sheet = answer_sheet or OFFICIAL_ANSWER_SHEET

    def correct(self, detected_answers: Dict[int, str]) -> Dict:
        """
        Corrige as respostas detectadas.
        Retorna dict com: acertos, erros, nota, detalhes, questões_faltando
        """
        gabarito = self.answer_sheet.get_gabarito()
        num_questions = self.answer_sheet.num_questions

        acertos = 0
        erros = 0
        detalhes = {}
        questoes_faltando = []

        for q in range(1, num_questions + 1):
            correta = gabarito.get(q, "")
            detectada = detected_answers.get(q, "")

            if not detectada:
                questoes_faltando.append(q)
                detalhes[q] = {"correta": correta, "detectada": "", "status": "não detectada"}
                continue

            if detectada == correta:
                acertos += 1
                detalhes[q] = {"correta": correta, "detectada": detectada, "status": "acerto"}
            else:
                erros += 1
                detalhes[q] = {"correta": correta, "detectada": detectada, "status": "erro"}

        nota = (acertos / num_questions) * 10 if num_questions > 0 else 0

        return {
            "acertos": acertos,
            "erros": erros,
            "nota": round(nota, 1),
            "detalhes": detalhes,
            "questoes_faltando": questoes_faltando,
            "total": num_questions,
            "completo": len(questoes_faltando) == 0
        }

    def get_result_text(self, result: Dict) -> str:
        """Gera texto formatado do resultado."""
        if not result["completo"]:
            return (
                f"Acertos: {result['acertos']} | Erros: {result['erros']} | "
                f"Faltando: {len(result['questoes_faltando'])}"
            )
        return (
            f"Resultado Final\n"
            f"Acertos: {result['acertos']}\n"
            f"Erros: {result['erros']}\n"
            f"Nota: {result['nota']:.1f}"
        )


def create_sample_gabarito() -> Dict[int, str]:
    """Cria um gabarito de exemplo para testes."""
    return {
        1: "A", 2: "B", 3: "C", 4: "D", 5: "E",
        6: "A", 7: "B", 8: "C", 9: "D", 10: "E",
        11: "E", 12: "D", 13: "C", 14: "B", 15: "A",
        16: "E", 17: "D", 18: "C", 19: "B", 20: "A"
    }