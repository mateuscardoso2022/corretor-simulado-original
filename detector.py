"""
Detector - Detecção de folha de gabarito e leitura de marcações.
Implementa visão computacional com OpenCV.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from config import (
    PROCESSING_CONFIG,
    DETECTION_CONFIG,
    ANSWER_SHEET_CONFIG,
    COLORS
)


class SheetDetector:
    """Detecta a folha de gabarito na imagem e corrige perspectiva."""

    def __init__(self):
        self.target_w = PROCESSING_CONFIG["target_width"]
        self.target_h = PROCESSING_CONFIG["target_height"]
        self.min_area = PROCESSING_CONFIG["min_contour_area"]
        self.max_area = PROCESSING_CONFIG["max_contour_area"]
        self.margin = PROCESSING_CONFIG["perspective_margin"]

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Pré-processamento: cinza, blur, canny."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, PROCESSING_CONFIG["blur_kernel"], 0)
        edges = cv2.Canny(
            blurred,
            PROCESSING_CONFIG["canny_low"],
            PROCESSING_CONFIG["canny_high"]
        )
        return edges

    def find_sheet_contour(self, edges: np.ndarray) -> Optional[np.ndarray]:
        """Encontra o contorno da folha (maior retângulo)."""
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_contour = None
        best_area = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area or area > self.max_area:
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4:
                if area > best_area:
                    best_area = area
                    best_contour = approx

        return best_contour

    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """Ordena pontos: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Aplica transformação de perspectiva para 'endireitar' a folha."""
        rect = self.order_points(pts.reshape(4, 2))
        (tl, tr, br, bl) = rect

        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_width = max(int(width_a), int(width_b))

        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_height = max(int(height_a), int(height_b))

        max_width = min(max_width, self.target_w)
        max_height = min(max_height, self.target_h)

        dst = np.array([
            [self.margin, self.margin],
            [max_width - self.margin, self.margin],
            [max_width - self.margin, max_height - self.margin],
            [self.margin, max_height - self.margin]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (max_width, max_height))
        return warped

    def detect_sheet(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str]:
        """
        Detecta a folha no frame.
        Retorna: (warped_image, contour, status_message)
        """
        edges = self.preprocess(frame)
        contour = self.find_sheet_contour(edges)

        if contour is None:
            return None, None, "Aproxime o gabarito"

        warped = self.four_point_transform(frame, contour)
        return warped, contour, "Folha detectada"


class AnswerDetector:
    """Detecta quais alternativas estão marcadas na folha corrigida."""

    def __init__(self):
        self.num_questions = ANSWER_SHEET_CONFIG["num_questions"]
        self.num_alternatives = ANSWER_SHEET_CONFIG["num_alternatives"]
        self.alternatives = ANSWER_SHEET_CONFIG["alternatives"]

        self.fill_threshold = DETECTION_CONFIG["fill_threshold"]
        self.min_diff = DETECTION_CONFIG["min_diff_threshold"]
        self.max_fill = DETECTION_CONFIG["max_fill_ratio"]
        self.min_pixels = DETECTION_CONFIG["min_fill_pixels"]
        self.bubble_ratio = DETECTION_CONFIG["bubble_size_ratio"]
        self.row_ratio = DETECTION_CONFIG["row_height_ratio"]

    def preprocess_warped(self, warped: np.ndarray) -> np.ndarray:
        """Pré-processa a folha corrigida para detecção de bolhas."""
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return thresh

    def get_bubble_regions(self, warped: np.ndarray) -> List[List[Tuple[int, int, int, int]]]:
        """
        Calcula regiões (x, y, w, h) de cada bolha baseado em proporções fixas.
        Retorna lista de listas: [questão][alternativa] = (x, y, w, h)
        """
        h, w = warped.shape[:2]

        # Área útil (removendo margens)
        margin_x = int(w * 0.1)
        margin_y = int(h * 0.1)
        usable_w = w - 2 * margin_x
        usable_h = h - 2 * margin_y

        bubble_w = int(usable_w * self.bubble_ratio)
        bubble_h = int(usable_h * self.bubble_ratio)
        row_h = int(usable_h * self.row_ratio)

        start_x = margin_x + int(usable_w * 0.15)
        start_y = margin_y + int(usable_h * 0.08)
        gap_x = int(usable_w * 0.14)
        gap_y = row_h

        regions = []
        for q in range(self.num_questions):
            q_regions = []
            for a in range(self.num_alternatives):
                x = start_x + a * gap_x
                y = start_y + q * gap_y
                q_regions.append((x, y, bubble_w, bubble_h))
            regions.append(q_regions)

        return regions

    def analyze_bubble(self, thresh: np.ndarray, x: int, y: int, w: int, h: int) -> float:
        """Analisa uma bolha e retorna ratio de preenchimento (0 a 1)."""
        x = max(0, x)
        y = max(0, y)
        w = min(w, thresh.shape[1] - x)
        h = min(h, thresh.shape[0] - y)

        if w <= 0 or h <= 0:
            return 0.0

        roi = thresh[y:y+h, x:x+w]
        total = w * h
        if total == 0:
            return 0.0

        filled = cv2.countNonZero(roi)
        return filled / total

    def detect_answers(self, warped: np.ndarray) -> Tuple[Dict[int, str], Dict[int, str], List[str]]:
        """
        Detecta respostas na folha corrigida.
        Retorna: (answers_dict, status_dict, messages_list)
        answers_dict: {question: 'A'/'B'/...}
        status_dict: {question: 'OK'/'DUAL'/'EMPTY'/'LOW_CONFIDENCE'}
        """
        thresh = self.preprocess_warped(warped)
        regions = self.get_bubble_regions(warped)

        answers = {}
        status = {}
        messages = []

        for q_idx, q_regions in enumerate(regions):
            q_num = q_idx + 1
            fills = []

            for a_idx, (x, y, w, h) in enumerate(q_regions):
                fill = self.analyze_bubble(thresh, x, y, w, h)
                fills.append(fill)

            max_fill = max(fills)
            max_idx = fills.index(max_fill)

            if max_fill < self.fill_threshold:
                status[q_num] = "EMPTY"
                answers[q_num] = ""
                continue

            # Verificar segunda maior
            sorted_fills = sorted(fills, reverse=True)
            if len(sorted_fills) > 1 and (sorted_fills[0] - sorted_fills[1]) < self.min_diff:
                status[q_num] = "DUAL"
                answers[q_num] = ""
                messages.append(f"Questão {q_num} possui duas marcações")
                continue

            if max_fill > self.max_fill:
                status[q_num] = "LOW_CONFIDENCE"
                answers[q_num] = ""
                messages.append(f"Questão {q_num}: marcação muito forte (possível erro)")
                continue

            answers[q_num] = self.alternatives[max_idx]
            status[q_num] = "OK"

        detected_count = sum(1 for v in answers.values() if v)
        messages.append(f"Questões detectadas: {detected_count}/{self.num_questions}")

        return answers, status, messages

    def draw_debug(self, warped: np.ndarray, answers: Dict[int, str], status: Dict[int, str]) -> np.ndarray:
        """Desenha debug na imagem corrigida."""
        debug = warped.copy()
        regions = self.get_bubble_regions(warped)

        for q_idx, q_regions in enumerate(regions):
            q_num = q_idx + 1
            for a_idx, (x, y, w, h) in enumerate(q_regions):
                color = COLORS["green"]
                if status.get(q_num) == "DUAL":
                    color = COLORS["red"]
                elif status.get(q_num) == "EMPTY":
                    color = COLORS["yellow"]
                elif status.get(q_num) == "LOW_CONFIDENCE":
                    color = COLORS["blue"]

                if answers.get(q_num) == self.alternatives[a_idx] and status.get(q_num) == "OK":
                    cv2.rectangle(debug, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(debug, self.alternatives[a_idx], (x, y-5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return debug


class FullDetector:
    """Detector completo: folha + respostas."""

    def __init__(self):
        self.sheet_detector = SheetDetector()
        self.answer_detector = AnswerDetector()
        self.last_warped = None
        self.last_contour = None

    def process(self, frame: np.ndarray) -> Dict:
        """
        Processa frame completo.
        Retorna dict com: warped, contour, answers, status, messages, debug_image
        """
        warped, contour, msg = self.sheet_detector.detect_sheet(frame)

        result = {
            "warped": None,
            "contour": contour,
            "answers": {},
            "status": {},
            "messages": [msg] if msg else [],
            "debug_image": frame.copy(),
            "sheet_found": warped is not None
        }

        if warped is not None:
            self.last_warped = warped
            self.last_contour = contour

            answers, status, msgs = self.answer_detector.detect_answers(warped)
            debug = self.answer_detector.draw_debug(warped, answers, status)

            result["warped"] = warped
            result["answers"] = answers
            result["status"] = status
            result["messages"].extend(msgs)
            result["debug_image"] = debug

            if all(v for v in answers.values()):
                result["messages"].append("GABARITO DETECTADO")

        elif self.last_warped is not None:
            # Manter última detecção válida por alguns frames
            result["warped"] = self.last_warped
            result["contour"] = self.last_contour
            result["messages"].append("Mantenha o gabarito dentro da área")

        return result