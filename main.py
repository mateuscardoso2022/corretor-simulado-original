"""
Corretor de Simulado - Interface Principal (Kivy)
Integra câmera, detecção e correção em tempo real.
"""

import os
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_NO_CONFIG'] = '1'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty
from kivy.core.window import Window

import cv2
import numpy as np
import threading
import time

from camera import Camera, CameraTextureProvider
from detector import FullDetector
from correction import Corrector, create_sample_gabarito
from answer_sheet import OFFICIAL_ANSWER_SHEET
from config import ANSWER_SHEET_CONFIG, COLORS


# KV Language para UI
KV = '''
<MenuScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 20

        Label:
            text: 'CORRETOR DE SIMULADO'
            font_size: 32
            bold: True
            size_hint_y: 0.3
            color: 0.2, 0.4, 0.8, 1

        Button:
            text: 'INICIAR CORREÇÃO'
            font_size: 24
            size_hint_y: 0.2
            on_press: root.start_camera()

        Button:
            text: 'CADASTRAR GABARITO'
            font_size: 24
            size_hint_y: 0.2
            on_press: root.goto_gabarito()

        Button:
            text: 'TESTE COM WEBCAM'
            font_size: 20
            size_hint_y: 0.15
            background_color: 0.3, 0.7, 0.3, 1
            on_press: root.start_camera(use_webcam=True)

        Label:
            id: status_label
            text: 'Pronto'
            font_size: 16
            size_hint_y: 0.15
            color: 0.4, 0.4, 0.4, 1


<GabaritoScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10

        Label:
            text: 'CADASTRAR GABARITO OFICIAL'
            font_size: 24
            bold: True
            size_hint_y: 0.1
            color: 0.2, 0.4, 0.8, 1

        ScrollView:
            GridLayout:
                id: gabarito_grid
                cols: 2
                spacing: 5
                size_hint_y: None
                height: self.minimum_height
                padding: 10

        BoxLayout:
            size_hint_y: 0.15
            spacing: 10
            Button:
                text: 'CARREGAR EXEMPLO'
                on_press: root.load_sample()
            Button:
                text: 'LIMPAR TUDO'
                on_press: root.clear_all()
            Button:
                text: 'VOLTAR'
                on_press: root.goto_menu()


<CameraScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 5

        BoxLayout:
            size_hint_y: 0.08
            padding: 10
            Label:
                id: camera_status
                text: 'Iniciando câmera...'
                font_size: 18
                bold: True
                color: 1, 1, 1, 1
            Button:
                text: 'VOLTAR'
                size_hint_x: 0.2
                on_press: root.stop_camera()

        Image:
            id: camera_image
            allow_stretch: True
            keep_ratio: True

        BoxLayout:
            id: results_container
            orientation: 'vertical'
            size_hint_y: 0.35
            padding: 10
            spacing: 5

            Label:
                id: detection_info
                text: 'Posicione o gabarito na área'
                font_size: 16
                bold: True
                color: 1, 1, 0, 1
                size_hint_y: 0.2

            ScrollView:
                GridLayout:
                    id: answers_grid
                    cols: 2
                    spacing: 3
                    size_hint_y: None
                    height: self.minimum_height
                    padding: 5

            Label:
                id: summary_label
                text: ''
                font_size: 16
                color: 0, 1, 0, 1
                size_hint_y: 0.2


<ResultScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 15

        Label:
            text: 'RESULTADO DA CORREÇÃO'
            font_size: 28
            bold: True
            size_hint_y: 0.15
            color: 0.2, 0.6, 0.2, 1

        Label:
            id: result_summary
            text: ''
            font_size: 22
            size_hint_y: 0.15
            color: 0.2, 0.2, 0.2, 1

        ScrollView:
            GridLayout:
                id: result_grid
                cols: 4
                spacing: 5
                size_hint_y: None
                height: self.minimum_height
                padding: 10

        BoxLayout:
            size_hint_y: 0.15
            spacing: 20
            Button:
                text: 'NOVA CORREÇÃO'
                font_size: 20
                on_press: root.new_correction()
            Button:
                text: 'VOLTAR AO MENU'
                font_size: 20
                on_press: root.goto_menu()
'''

Builder.load_string(KV)


class MenuScreen(Screen):
    def start_camera(self, use_webcam=False):
        app = App.get_running_app()
        app.use_webcam = use_webcam
        self.manager.current = 'camera'

    def goto_gabarito(self):
        self.manager.current = 'gabarito'


class GabaritoScreen(Screen):
    def on_enter(self):
        self.build_grid()

    def build_grid(self):
        grid = self.ids.gabarito_grid
        grid.clear_widgets()

        num_q = ANSWER_SHEET_CONFIG["num_questions"]
        alternatives = ANSWER_SHEET_CONFIG["alternatives"]

        gabarito = OFFICIAL_ANSWER_SHEET.get_gabarito()

        for q in range(1, num_q + 1):
            lbl = Label(text=f'{q}', font_size=18, size_hint_x=0.2, bold=True)
            grid.add_widget(lbl)

            box = BoxLayout(spacing=2)
            current = gabarito.get(q, "")

            for alt in alternatives:
                btn = ToggleButton(
                    text=alt,
                    font_size=16,
                    group=f'q{q}',
                    size_hint_x=0.16,
                    state='down' if alt == current else 'normal'
                )
                btn.question = q
                btn.alternative = alt
                btn.bind(on_press=self.on_alternative_select)
                box.add_widget(btn)
            grid.add_widget(box)

    def on_alternative_select(self, btn):
        if btn.state == 'down':
            OFFICIAL_ANSWER_SHEET.set_answer(btn.question, btn.alternative)

    def load_sample(self):
        OFFICIAL_ANSWER_SHEET.set_gabarito(create_sample_gabarito())
        self.build_grid()

    def clear_all(self):
        OFFICIAL_ANSWER_SHEET._gabarito.clear()
        self.build_grid()

    def goto_menu(self):
        self.manager.current = 'menu'


class ToggleButton(Button):
    question = NumericProperty(0)
    alternative = StringProperty('')


class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera = None
        self.detector = FullDetector()
        self.corrector = Corrector()
        self.running = False
        self.last_results = {}

    def on_enter(self):
        self.start_camera()

    def start_camera(self):
        app = App.get_running_app()
        cam_index = 0 if getattr(app, 'use_webcam', True) else 0

        self.camera = Camera(cam_index)
        if not self.camera.start():
            self.ids.camera_status.text = 'Erro ao abrir câmera'
            return

        self.running = True
        self.ids.camera_status.text = 'Câmera ativa - Posicione o gabarito'
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def stop_camera(self):
        self.running = False
        Clock.unschedule(self.update_frame)
        if self.camera:
            self.camera.stop()
            self.camera = None
        self.manager.current = 'menu'

    def update_frame(self, dt):
        if not self.running or not self.camera:
            return

        frame = self.camera.get_frame()
        if frame is None:
            return

        # Atualizar preview da câmera
        texture = CameraTextureProvider.frame_to_texture(frame)
        if texture:
            self.ids.camera_image.texture = texture

        # Processar apenas alguns frames
        if self.camera.should_process():
            self.process_frame_async(frame)

    def process_frame_async(self, frame):
        """Processa frame em thread separada para não travar UI."""
        threading.Thread(target=self._process_frame, args=(frame,), daemon=True).start()

    def _process_frame(self, frame):
        result = self.detector.process(frame)

        # Atualizar UI na thread principal
        Clock.schedule_once(lambda dt: self.update_ui(result), 0)

    def update_ui(self, result):
        if not self.running:
            return

        # Status da detecção
        messages = result.get("messages", [])
        if messages:
            self.ids.detection_info.text = " | ".join(messages[-3:])

        # Grid de respostas
        grid = self.ids.answers_grid
        grid.clear_widgets()

        answers = result.get("answers", {})
        status = result.get("status", {})

        for q in range(1, ANSWER_SHEET_CONFIG["num_questions"] + 1):
            ans = answers.get(q, "")
            st = status.get(q, "")

            q_label = Label(text=f'Q{q}', font_size=14, bold=True, size_hint_x=0.3)

            if ans:
                if st == "OK":
                    color = (0, 1, 0, 1)
                    txt = f'→ {ans} ✓'
                elif st == "DUAL":
                    color = (1, 0, 0, 1)
                    txt = f'→ {ans} (dupla)'
                else:
                    color = (1, 0.5, 0, 1)
                    txt = f'→ {ans} ?'
            else:
                color = (0.7, 0.7, 0.7, 1)
                txt = '—'

            ans_label = Label(text=txt, font_size=14, color=color, size_hint_x=0.7)
            grid.add_widget(q_label)
            grid.add_widget(ans_label)

        # Resumo
        detected = sum(1 for v in answers.values() if v)
        total = ANSWER_SHEET_CONFIG["num_questions"]
        self.ids.summary_label.text = f'Detectadas: {detected}/{total}'

        # Se completo e tem gabarito, mostrar resultado
        if detected == total and OFFICIAL_ANSWER_SHEET.is_complete():
            self.show_result(answers)

    def show_result(self, answers):
        self.running = False
        Clock.unschedule(self.update_frame)

        result = self.corrector.correct(answers)
        app = App.get_running_app()
        app.last_result = result
        app.last_answers = answers
        self.manager.current = 'result'


class ResultScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        result = getattr(app, 'last_result', None)
        answers = getattr(app, 'last_answers', {})

        if result:
            self.ids.result_summary.text = app.corrector.get_result_text(result)

            grid = self.ids.result_grid
            grid.clear_widgets()

            # Cabeçalho
            for h in ['Questão', 'Sua', 'Gabarito', 'Status']:
                grid.add_widget(Label(text=h, font_size=16, bold=True, color=(0.2,0.2,0.2,1)))

            for q in range(1, ANSWER_SHEET_CONFIG["num_questions"] + 1):
                det = result["detalhes"][q]
                grid.add_widget(Label(text=str(q), font_size=14))
                grid.add_widget(Label(text=det["detectada"] or "—", font_size=14))
                grid.add_widget(Label(text=det["correta"] or "—", font_size=14))

                status_lbl = Label(font_size=14, bold=True)
                if det["status"] == "acerto":
                    status_lbl.text = "✓"
                    status_lbl.color = (0, 0.7, 0, 1)
                elif det["status"] == "erro":
                    status_lbl.text = "✗"
                    status_lbl.color = (0.8, 0, 0, 1)
                else:
                    status_lbl.text = "—"
                    status_lbl.color = (0.5, 0.5, 0.5, 1)
                grid.add_widget(status_lbl)

    def new_correction(self):
        self.manager.current = 'camera'

    def goto_menu(self):
        self.manager.current = 'menu'


class CorretorApp(App):
    use_webcam = True
    last_result = None
    last_answers = {}
    corrector = Corrector()

    def build(self):
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GabaritoScreen(name='gabarito'))
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ResultScreen(name='result'))
        return sm

    def on_stop(self):
        # Limpar ao fechar
        pass


if __name__ == '__main__':
    CorretorApp().run()