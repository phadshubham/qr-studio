from flask import Flask, render_template, request, jsonify
import os
import qrcode
from PIL import Image, ImageDraw
import math

app = Flask(__name__)

UPLOAD_FOLDER = "static/generated"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

THEMES = {
    "classic": ("#000000", "#ffffff"),
    "midnight": ("#ffffff", "#0f172a"),
    "ocean": ("#00c6ff", "#002b5b"),
    "sunset": ("#ff512f", "#1e1e2f"),
    "forest": ("#14532d", "#dcfce7"),
    "royal": ("#7c3aed", "#f5f3ff"),
}


# 🔹 Helper: Hex to RGB
def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))


# 🔹 Gradient Engine
def apply_gradient(mask_img, color1, color2, gradient_type="vertical"):
    width, height = mask_img.size
    gradient = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(gradient)

    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    for y in range(height):
        for x in range(width):

            if gradient_type == "vertical":
                ratio = y / height
            elif gradient_type == "horizontal":
                ratio = x / width
            elif gradient_type == "diagonal":
                ratio = (x + y) / (width + height)
            elif gradient_type == "radial":
                center_x, center_y = width / 2, height / 2
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                max_dist = math.sqrt(center_x ** 2 + center_y ** 2)
                ratio = dist / max_dist
            else:
                ratio = y / height

            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)

            draw.point((x, y), fill=(r, g, b))

    final = Image.new("RGB", (width, height), "white")
    final.paste(gradient, mask=mask_img)

    return final


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.form["data"]
    selected_theme = request.form.get("theme")
    use_gradient = request.form.get("gradient")
    gradient_type = request.form.get("gradient_type", "vertical")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(data)
    qr.make(fit=True)

    mask_img = qr.make_image(fill_color="black", back_color="white").convert("L")

    # 🎨 Gradient overrides theme
    if use_gradient == "on":
        grad_color1 = request.form.get("grad_color1", "#ff512f")
        grad_color2 = request.form.get("grad_color2", "#0072ff")
        img = apply_gradient(mask_img, grad_color1, grad_color2, gradient_type)
    else:
        if selected_theme in THEMES:
            qr_color, bg_color = THEMES[selected_theme]
        else:
            qr_color = request.form.get("qr_color", "#000000")
            bg_color = request.form.get("bg_color", "#ffffff")

        img = qr.make_image(fill_color=qr_color, back_color=bg_color).convert("RGB")

    file_path = os.path.join(UPLOAD_FOLDER, "qr_code.png")
    img.save(file_path)

    return jsonify({"image_url": "/static/generated/qr_code.png"})


if __name__ == "__main__":
    app.run(debug=True)