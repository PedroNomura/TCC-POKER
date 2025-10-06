from fer import FER
import cv2

# Inicializa detector e webcam
detector = FER()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detecta emoções no frame
    results = detector.detect_emotions(frame)

    # Para cada rosto detectado
    for result in results:
        (x, y, w, h) = result["box"]
        emotions = result["emotions"]

        # Emoção dominante
        dominant_emotion = max(emotions, key=emotions.get)
        confidence = emotions[dominant_emotion]

        # Desenha o retângulo e a emoção
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"{dominant_emotion} ({confidence:.2f})",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    # Mostra o vídeo
    cv2.imshow("Reconhecimento de Emoções - FER", frame)

    # Sai com 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Libera recursos
cap.release()
cv2.destroyAllWindows()
