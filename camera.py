"""
Módulo de Câmera - Captura de vídeo da webcam.
Suporta modo teste (webcam PC) e modo Android (para buildozer).
"""

import cv2
import numpy as np
from config import CAMERA_CONFIG


class Camera:
    """Gerencia captura de vídeo da webcam."""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: cv2.VideoCapture = None
        self.is_running = False
        self.frame_count = 0
        self._last_frame = None

    def start(self) -> bool:
        """Inicia a captura da câmera."""
        if self.is_running:
            return True

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"Erro: Não foi possível abrir a câmera {self.camera_index}")
                return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG["width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG["height"])
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_CONFIG["fps"])

        self.is_running = True
        print("Câmera iniciada com sucesso")
        return True

    def stop(self):
        """Para a captura da câmera."""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        print("Câmera parada")

    def get_frame(self) -> np.ndarray:
        """Retorna o frame atual da câmera."""
        if not self.is_running or not self.cap:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        self.frame_count += 1
        self._last_frame = frame
        return frame

    def should_process(self) -> bool:
        """Verifica se deve processar este frame (otimização)."""
        return self.frame_count % CAMERA_CONFIG["process_every_n_frames"] == 0

    def get_last_frame(self) -> np.ndarray:
        """Retorna o último frame capturado."""
        return self._last_frame

    def get_frame_shape(self):
        """Retorna dimensões do frame."""
        if self.cap:
            return (
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
        return (CAMERA_CONFIG["width"], CAMERA_CONFIG["height"])

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class CameraTextureProvider:
    """Converter frames OpenCV para textura Kivy."""

    @staticmethod
    def frame_to_texture(frame: np.ndarray):
        """Converte frame BGR numpy para textura Kivy."""
        from kivy.graphics.texture import Texture
        if frame is None:
            return None

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.flip(frame_rgb, 0)

        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        return texture