"""
Teste rápido da detecção sem interface Kivy.
Rode: python test_detector.py
"""

import cv2
import numpy as np
from camera import Camera
from detector import FullDetector
from correction import Corrector, create_sample_gabarito
from answer_sheet import OFFICIAL_ANSWER_SHEET

# Carregar gabarito de teste
OFFICIAL_ANSWER_SHEET.set_gabarito(create_sample_gabarito())

camera = Camera(0)
if not camera.start():
    print("Erro: Webcam não encontrada")
    exit(1)

detector = FullDetector()
corrector = Corrector()

print("=== TESTE DO DETECTOR ===")
print("Pressione 'q' para sair, 's' para salvar frame, 'r' para resultado")
print()

frame_count = 0

while True:
    frame = camera.get_frame()
    if frame is None:
        continue

    frame_count += 1

    # Processar a cada 3 frames
    if frame_count % 3 == 0:
        result = detector.process(frame)

        # Mostrar status
        msgs = result.get("messages", [])
        if msgs:
            print(f"\r{' | '.join(msgs[-2:])}", end="", flush=True)

        # Se detectou tudo, mostrar correção
        answers = result.get("answers", {})
        detected = sum(1 for v in answers.values() if v)
        if detected == 20 and OFFICIAL_ANSWER_SHEET.is_complete():
            correction = corrector.correct(answers)
            print(f"\n\n=== RESULTADO ===")
            print(f"Acertos: {correction['acertos']} | Erros: {correction['erros']} | Nota: {correction['nota']}")
            for q in range(1, 21):
                d = correction['detalhes'][q]
                status = "✓" if d['status']=='acerto' else "✗" if d['status']=='erro' else "—"
                print(f"  Q{q}: {d['detectada'] or '?'} (gabarito: {d['correta']}) {status}")

    # Preview
    cv2.imshow('Corretor - Preview (q=sair)', frame)

    if 'result' in locals() and result.get("warped") is not None:
        cv2.imshow('Corretor - Folha Corrigida', result["warped"])
        if result.get("debug_image") is not None:
            cv2.imshow('Corretor - Debug', result["debug_image"])

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite('frame_teste.jpg', frame)
        print("\nFrame salvo como frame_teste.jpg")
    elif key == ord('r') and detected == 20:
        correction = corrector.correct(answers)
        print(f"\n=== RESULTADO ===")
        print(f"Acertos: {correction['acertos']} | Erros: {correction['erros']} | Nota: {correction['nota']}")

camera.stop()
cv2.destroyAllWindows()
print("\nTeste finalizado.")