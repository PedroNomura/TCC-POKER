from deepface import DeepFace
res = DeepFace.analyze("foto.jpg", actions=["emotion"], enforce_detection=False)
print(res[0]["emotion"])
