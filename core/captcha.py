import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

CAPTCHA_CACHE = {}

CHAR_COUNT = 4


def generate_captcha_text():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=CHAR_COUNT))


def create_captcha_image(text):
    FONT_SIZE = 36
    PADDING_X = 16
    PADDING_Y = 12
    width = 200
    height = 60

    img = Image.new('RGB', (width, height), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    except OSError:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2 - bbox[0]
    y = (height - text_height) // 2 - bbox[1]

    draw.text((x, y), text, fill=(30, 40, 80), font=font)

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generate_captcha(captcha_id=None):
    import uuid
    if not captcha_id:
        captcha_id = str(uuid.uuid4())[:8]
    text = generate_captcha_text()
    image_buf = create_captcha_image(text)
    CAPTCHA_CACHE[captcha_id] = {'text': text.upper()}
    return captcha_id, image_buf, text


def verify_captcha(captcha_id, user_input):
    if not captcha_id or not user_input:
        return False
    cached = CAPTCHA_CACHE.get(captcha_id)
    if not cached:
        return False
    result = cached['text'] == user_input.strip().upper()
    del CAPTCHA_CACHE[captcha_id]
    return result
