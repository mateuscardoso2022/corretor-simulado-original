"""
Configurações do Corretor de Simulado
Modelo do cartão-resposta separado da lógica de processamento.
"""

# Modelo do cartão-resposta
ANSWER_SHEET_CONFIG = {
    "num_questions": 20,
    "alternatives": ["A", "B", "C", "D", "E"],
    "num_alternatives": 5,
}

# Configurações de processamento de imagem
PROCESSING_CONFIG = {
    "target_width": 800,
    "target_height": 1000,
    "blur_kernel": (5, 5),
    "canny_low": 50,
    "canny_high": 150,
    "min_contour_area": 10000,
    "max_contour_area": 500000,
    "perspective_margin": 20,
}

# Configurações de detecção de marcações
DETECTION_CONFIG = {
    "fill_threshold": 0.35,
    "min_diff_threshold": 0.15,
    "max_fill_ratio": 0.85,
    "min_fill_pixels": 50,
    "bubble_size_ratio": 0.015,
    "row_height_ratio": 0.045,
}

# Configurações de câmera
CAMERA_CONFIG = {
    "width": 1280,
    "height": 720,
    "fps": 30,
    "process_every_n_frames": 3,
}

# Cores para debug (BGR)
COLORS = {
    "green": (0, 255, 0),
    "red": (0, 0, 255),
    "blue": (255, 0, 0),
    "yellow": (0, 255, 255),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}