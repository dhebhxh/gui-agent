# Functional tests: mss / PyAutoGUI / EasyOCR / OpenCV / Transformers / LangChain

import os
import torch
import cv2
import numpy as np
import mss
import pyautogui
import easyocr

from transformers import BertConfig, BertModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

SCREENSHOT_PATH = "test_screenshot.png"
TEST_IMG = "test_cv.png"


def test_gui_ocr():
    """mss + PyAutoGUI + EasyOCR functional test"""
    print("=" * 50)
    print("[1/5] mss + PyAutoGUI + EasyOCR")
    print("=" * 50)

    # Screen capture (use MSS class to avoid deprecation warning)
    with mss.MSS() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        print("Screenshot shape:", img.shape)
        cv2.imwrite(SCREENSHOT_PATH, img)

    # Screen resolution and mouse position
    print("Screen size:", pyautogui.size())
    print("Mouse position:", pyautogui.position())

    # OCR (downloads models on first run, ~100 MB)
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=torch.cuda.is_available())
    result = reader.readtext(SCREENSHOT_PATH)
    print("OCR detected", len(result), "text regions")

    # GPU availability
    print("CUDA available:", torch.cuda.is_available())
    print("GPU name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")

    print("GUI + OCR test OK\n")


def test_opencv():
    """OpenCV functional test"""
    print("=" * 50)
    print("[2/5] OpenCV")
    print("=" * 50)

    # Create a test image (gray background + red rectangle)
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    img[:] = (200, 200, 200)
    cv2.rectangle(img, (50, 50), (200, 200), (0, 0, 255), -1)

    # Save and load
    cv2.imwrite(TEST_IMG, img)
    loaded = cv2.imread(TEST_IMG)
    print("Image shape:", loaded.shape)

    # Color space conversion (BGR -> Grayscale)
    gray = cv2.cvtColor(loaded, cv2.COLOR_BGR2GRAY)
    print("Grayscale shape:", gray.shape)

    # Image filtering (Gaussian blur)
    cv2.GaussianBlur(loaded, (7, 7), 0)
    print("Gaussian blur: OK")

    # Edge detection (Canny)
    edges = cv2.Canny(gray, 50, 150)
    print("Edge detection: OK, edge pixels =", int(np.sum(edges > 0)))

    # Contour analysis
    mask = cv2.inRange(loaded, (0, 0, 200), (50, 50, 255))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print("Contours detected:", len(contours))

    print("OpenCV test OK\n")


def test_transformers():
    """Transformers functional test (no download, no cache left behind)"""
    print("=" * 50)
    print("[3/5] Transformers")
    print("=" * 50)

    # Build a tiny randomly-initialized BERT locally (no download)
    config = BertConfig(
        vocab_size=1000,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=2,
        intermediate_size=128,
    )
    model = BertModel(config)
    model.eval()

    # Forward pass with dummy input
    dummy_input = torch.randint(0, 1000, (1, 8))  # batch=1, seq_len=8
    with torch.no_grad():
        output = model(dummy_input)

    print("Output shape:", output.last_hidden_state.shape)
    print("Device:", "GPU" if torch.cuda.is_available() else "CPU")

    print("Transformers test OK\n")


def test_langchain():
    """LangChain functional test (no real LLM call, no API key required)"""
    print("=" * 50)
    print("[4/5] LangChain")
    print("=" * 50)

    # Prompt template
    prompt = ChatPromptTemplate.from_template("Describe {topic} in one sentence.")

    # Mock LLM: ChatPromptTemplate produces a ChatPromptValue, which is a list
    # of messages. Simulate a chat model by returning a plain string response.
    def fake_llm(messages):
        # Extract the last message content as the prompt text
        last_message = messages.messages[-1].content
        return f"[Mock answer] An introduction to \"{last_message}\"."

    # Output parser
    parser = StrOutputParser()

    # Assemble chain: prompt | llm | parser
    chain = prompt | RunnableLambda(fake_llm) | parser

    # Invoke
    result = chain.invoke({"topic": "GUI agents"})
    print("Chain result:", result)

    # Batch
    batch_result = chain.batch([{"topic": "PyTorch"}, {"topic": "OpenCV"}])
    print("Batch result count:", len(batch_result))

    print("LangChain test OK\n")


def cleanup():
    """Clean up intermediate artifacts"""
    print("=" * 50)
    print("[5/5] Cleanup")
    print("=" * 50)

    for path in (SCREENSHOT_PATH, TEST_IMG):
        if os.path.exists(path):
            os.remove(path)
            print("Removed:", path)


if __name__ == "__main__":
    try:
        test_gui_ocr()
        test_opencv()
        test_transformers()
        test_langchain()
        print("=" * 50)
        print("All functional tests passed")
        print("=" * 50)
    finally:
        cleanup()