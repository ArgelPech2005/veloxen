import pyotp
import base64
import qrcode
from io import BytesIO
secret = pyotp.random_base32()
totp = pyotp.TOTP(secret)
uri = totp.provisioning_uri(name="Juan", issuer_name="ElAmigo 7")

img = qrcode.make(uri)
buf = BytesIO()
img.save(buf)
img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

print(img_b64)