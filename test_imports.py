import torch
print("PyTorch:", torch.__version__, "| CUDA:", torch.cuda.is_available())

import cv2
print("OpenCV:", cv2.__version__)

import mss
print("mss: OK")

import pyautogui
print("PyAutoGUI:", pyautogui.__version__)

import easyocr
print("EasyOCR: OK")

import langchain
print("LangChain:", langchain.__version__)

import transformers
print("Transformers:", transformers.__version__)

print("\nAll imports OK")