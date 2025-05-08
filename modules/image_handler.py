from PIL import Image
from io import BytesIO
import base64

def handle_image(image):
    image = Image.open(image).convert('RGB')

    buffer = BytesIO()
    image.save(buffer,format="JPEG")
    buf_image = buffer.getvalue()
    return base64.b64encode(buf_image)