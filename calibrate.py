"""
Calibrador Visual de Bolhas
- Mostra folha corrigida com grid numerado
- Clique nas bolhas para capturar coordenadas reais
- Salva configuração calibrada em config_calibrated.py
"""

import cv2
import numpy as np
import json
from camera import Camera
from detector import SheetDetector
from config import ANSWER_SHEET_CONFIG, PROCESSING_CONFIG


class BubbleCalibrator:
    def __init__(self):
        self.camera = Camera(0)
        self.sheet_detector = SheetDetector()
        self.num_questions = ANSWER_SHEET_CONFIG["num_questions"]
        self.num_alternatives = ANSWER_SHEET_CONFIG["num_alternatives"]
        self.alternatives = ANSWER_SHEET_CONFIG["alternatives"]

        # Estado da calibração
        self.calibrated_regions = []  # [(x, y, w, h), ...] por questão
        self.current_question = 0
        self.current_alternative = 0
        self.waiting_for_click = False
        self.last_warped = None
        self.click_points = []

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and self.waiting_for_click:
            self.click_points.append((x, y))
            print(f"  Clique {len(self.click_points)}: ({x}, {y})")

            if len(self.click_points) == 2:
                x1, y1 = self.click_points[0]
                x2, y2 = self.click_points[1]
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)

                # Garantir ordem: A, B, C, D, E
                while len(self.calibrated_regions) <= self.current_question:
                    self.calibrated_regions.append([])

                self.calibrated_regions[self.current_question].append((x, y, w, h))
                print(f"    → Q{self.current_question+1} {self.alternatives[self.current_alternative]}: ({x}, {y}, {w}, {h})")

                self.click_points = []
                self.next_bubble()

    def next_bubble(self):
        self.current_alternative += 1
        if self.current_alternative >= self.num_alternatives:
            self.current_alternative = 0
            self.current_question += 1

        if self.current_question >= self.num_questions:
            self.waiting_for_click = False
            self.save_calibration()
        else:
            self.waiting_for_click = True
            alt = self.alternatives[self.current_alternative]
            print(f"\n=== Q{self.current_question+1} - {alt} ===")
            print("Clique: canto superior esquerdo → canto inferior direito da bolha")

    def draw_grid(self, warped):
        """Desenha grid de calibração na folha corrigida."""
        vis = warped.copy()
        h, w = vis.shape[:2]

        # Desenhar regiões já calibradas
        for q_idx, q_regions in enumerate(self.calibrated_regions):
            for a_idx, (x, y, bw, bh) in enumerate(q_regions):
                color = (0, 255, 0) if q_idx < self.current_question or (q_idx == self.current_question and a_idx < self.current_alternative) else (0, 255, 255)
                cv2.rectangle(vis, (x, y), (x+bw, y+bh), color, 2)
                cv2.putText(vis, f"{q_idx+1}{self.alternatives[a_idx]}", (x, y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Destacar bolha atual
        if self.waiting_for_click and self.current_question < self.num_questions:
            if self.current_question < len(self.calibrated_regions) and self.current_alternative < len(self.calibrated_regions[self.current_question]):
                pass  # já desenhou acima
            else:
                # Desenhar estimativa baseada em proporção
                est_x = int(w * 0.2) + self.current_alternative * int(w * 0.14)
                est_y = int(h * 0.1) + self.current_question * int(h * 0.045)
                est_w = int(w * 0.015)
                est_h = int(h * 0.015)
                cv2.rectangle(vis, (est_x, est_y), (est_x+est_w, est_y+est_h), (0, 0, 255), 2)
                cv2.putText(vis, f"{self.current_question+1}{self.alternatives[self.current_alternative]}?", (est_x, est_y-5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Instruções
        info = f"Calibrando: Q{self.current_question+1}/{self.num_questions} - {self.alternatives[self.current_alternative] if self.waiting_for_click else 'CONCLUÍDO'}"
        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)

        return vis

    def save_calibration(self):
        """Salva calibração em arquivo Python."""
        print("\n=== CALIBRAÇÃO CONCLUÍDA ===")

        # Gerar código Python para get_bubble_regions()
        code = self.generate_code()

        with open("config_calibrated.py", "w", encoding="utf-8") as f:
            f.write(code)

        print("Salvo em: config_calibrated.py")
        print("\nPara usar: edite detector.py e substitua get_bubble_regions() pelo conteúdo de config_calibrated.py")

    def generate_code(self) -> str:
        """Gera código Python das regiões calibradas."""
        lines = [
            "# Regiões calibradas - gerado automaticamente",
            "# Substitua get_bubble_regions() em detector.py por este código:",
            "",
            "def get_bubble_regions_calibrated(warped):",
            '    """Retorna regiões (x, y, w, h) calibradas manualmente."""',
            "    regions = [",
        ]

        for q_idx, q_regions in enumerate(self.calibrated_regions):
            lines.append(f"        [  # Q{q_idx+1}")
            for a_idx, (x, y, w, h) in enumerate(q_regions):
                lines.append(f"            ({x}, {y}, {w}, {h}),  # {self.alternatives[a_idx]}")
            lines.append("        ],")

        lines.extend([
            "    ]",
            "    return regions",
            "",
            "# --- Fim da calibração ---",
        ])

        return "\n".join(lines)

    def run(self):
        print("=== CALIBRADOR DE BOLHAS ===")
        print("1. Posicione o cartão-resposta na frente da câmera")
        print("2. A folha será detectada e endireitada automaticamente")
        print("3. Clique em cada bolha: canto sup. esq. → canto inf. dir.")
        print("4. Ordem: Q1-A, Q1-B, Q1-C, Q1-D, Q1-E, Q2-A, ...")
        print("5. Pressione ESPAÇO para pular bolha, 'r' para reiniciar, 'q' para sair")
        print()

        if not self.camera.start():
            print("Erro: Webcam não encontrada")
            return

        cv2.namedWindow('Calibrador', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Calibrador', self.mouse_callback)

        self.waiting_for_click = True
        print(f"\n=== Q1 - A ===")
        print("Clique: canto superior esquerdo → canto inferior direito da bolha")

        while True:
            frame = self.camera.get_frame()
            if frame is None:
                continue

            # Detectar folha
            warped, contour, msg = self.sheet_detector.detect_sheet(frame)

            if warped is not None:
                self.last_warped = warped
                vis = self.draw_grid(warped)
                cv2.imshow('Calibrador', vis)

                # Mostrar preview da câmera pequeno
                small = cv2.resize(frame, (320, 180))
                cv2.imshow('Camera', small)
            else:
                cv2.imshow('Calibrador', frame)
                cv2.putText(frame, msg, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Pular bolha
                if self.waiting_for_click:
                    self.click_points = []
                    self.next_bubble()
            elif key == ord('r'):  # Reiniciar
                self.calibrated_regions = []
                self.current_question = 0
                self.current_alternative = 0
                self.click_points = []
                self.waiting_for_click = True
                print("\n=== REINICIADO ===")
                print(f"=== Q1 - A ===")

        self.camera.stop()
        cv2.destroyAllWindows()


def quick_test_regions():
    """Teste rápido: desenha grid estimado na folha detectada."""
    camera = Camera(0)
    sheet_detector = SheetDetector()

    if not camera.start():
        return

    cv2.namedWindow('Teste Grid', cv2.WINDOW_NORMAL)

    while True:
        frame = camera.get_frame()
        if frame is None:
            continue

        warped, contour, msg = sheet_detector.detect_sheet(frame)

        if warped is not None:
            h, w = warped.shape[:2]
            vis = warped.copy()

            # Grid estimado (mesmo código do detector.py)
            margin_x = int(w * 0.1)
            margin_y = int(h * 0.1)
            usable_w = w - 2 * margin_x
            usable_h = h - 2 * margin_y

            bubble_w = int(usable_w * 0.015)
            bubble_h = int(usable_h * 0.015)

            start_x = margin_x + int(usable_w * 0.15)
            start_y = margin_y + int(usable_h * 0.08)
            gap_x = int(usable_w * 0.14)
            gap_y = int(usable_h * 0.045)

            for q in range(20):
                for a in range(5):
                    x = start_x + a * gap_x
                    y = start_y + q * gap_y
                    cv2.rectangle(vis, (x, y), (x+bubble_w, y+bubble_h), (0, 255, 0), 1)
                    cv2.putText(vis, f"{q+1}{['A','B','C','D','E'][a]}", (x, y-2),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)

            cv2.imshow('Teste Grid', vis)
        else:
            cv2.imshow('Teste Grid', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    camera.stop()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        quick_test_regions()
    else:
        cal = BubbleCalibrator()
        cal.run()