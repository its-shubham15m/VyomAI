from io import BytesIO
import streamlit as st
import qrcode
from qrcode.image.styledpil import StyledPilImage
import qrcode.image.styles.colormasks as masks
import qrcode.image.svg as svg
from models.res.config import mods_dict

def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    return tuple(int(hex[i:i + 2], 16) for i in (0, 2, 4))


def image_to_bytes(img):
    bio = BytesIO()
    img.save(bio, format='PNG')
    return bio.getvalue()

def setup_qrcode(text, dict_format, format, color, resolution, modStyle):
    # Construct the QR Code according to the parameters selected by user
    # Setting box size to 36 minium value defined empirically to make the qr image be slightly above the maximum resolution of 1024 x 1024

    qr = qrcode.QRCode(
        box_size=36,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        mask_pattern=0,
        border=4,
    )

    qr.add_data(text)
    qr.make(fit=True)

    if format == 'png':

        img_final = qr.make_image(
            image_factory=StyledPilImage,
            color_mask=masks.SolidFillColorMask(
                back_color=(255, 255, 255),
                front_color=hex_to_rgb(color),
            ),
            module_drawer=mods_dict[format][modStyle],
        )

        w, h = resolution.replace(" ", "").split("x")
        img_final = img_final.resize((int(w), int(h)))

    elif format == 'svg':

        img_final = qr.make_image(
            image_factory=svg.SvgPathFillImage,
            module_drawer=dict_format[modStyle],
        )

    download_image(img_final, format, color, "qrcode")


# Função para download da imagem
def download_image(img, format, color, filename):
    filename = f'{filename}.{format}'

    if format == 'png':

        st.download_button(
            label="Download",
            data=image_to_bytes(img),
            file_name=filename,
            mime='image/png',
            type='secondary',
        )

    elif format == 'svg':

        img.save(filename)

        with open(filename, "r") as qr_img:
            content = qr_img.read()

        content = content.replace("#000000", color)

        with open(filename, "w+") as qr_img:
            qr_img.write(content)
            st.download_button(
                label="Download",
                data=content,
                file_name=filename,
                mime='image/svg+xml',
                type='secondary',
            )