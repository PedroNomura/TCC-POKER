import cv2
import time
from deepface import DeepFace
import numpy as np

# pré-carrega modelo de emoção
preload_frame = np.zeros((100, 100, 3), dtype=np.uint8)
DeepFace.analyze(preload_frame, actions=["emotion"], enforce_detection=False)

def pegar_probabilidades_webcam_tempo(cap, duracao=5, pesos=None):
    if not cap.isOpened():
        print("Erro: webcam não está aberta.")
        return None

    inicio = time.time()
    lista_probs = []
    frame_count = 0

    while time.time() - inicio < duracao:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            resultado = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=True)
            if isinstance(resultado, list):
                resultado = resultado[0]

            # Ignora o primeiro frame para evitar atraso inicial
            if frame_count > 0:
                # Remove "neutral" antes de armazenar
                emo_frame = {k: v for k, v in resultado["emotion"].items() if k != "neutral"}
                lista_probs.append(emo_frame)

            frame_count += 1

        except Exception as e:
            print("Erro em um frame:", e)

    if not lista_probs:
        return None

    # calcular média das probabilidades (ignorando "neutral")
    chaves = lista_probs[0].keys()
    medias = {chave: np.mean([d[chave] for d in lista_probs]) for chave in chaves}

    # aplicar pesos se fornecidos
    if pesos:
        for emo, peso in pesos.items():
            if emo in medias:
                medias[emo] *= peso

    return medias


# ---- exemplo de uso ----
cap = cv2.VideoCapture(0)
time.sleep(0.5)

# pesos opcionais
pesos = {
    "happy": 1,
    "sad": 1,
    "angry": 1,
    "fear": 1,
    "disgust": 1,
    "surprise": 1
}

probs = pegar_probabilidades_webcam_tempo(cap, duracao=5, pesos=pesos)
cap.release()

if probs:
    print("Médias ponderadas das probabilidades em 5s:", probs)
    print("Expressão dominante:", max(probs, key=probs.get))
