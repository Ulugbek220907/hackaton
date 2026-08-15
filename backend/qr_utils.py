import os
import qrcode

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
QR_DIR = os.path.join(STATIC_DIR, "qr_codes")


def ensure_qr_dir():
    os.makedirs(QR_DIR, exist_ok=True)


def generate_qr_code_image(code: str) -> str:
    """
    Generates a PNG image for the given unique code token,
    saves it in backend/static/qr_codes/, and returns the relative URL path.
    """
    ensure_qr_dir()
    file_filename = f"{code}.png"
    file_path = os.path.join(QR_DIR, file_filename)

    if not os.path.exists(file_path):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(file_path)

    return f"/static/qr_codes/{file_filename}"
