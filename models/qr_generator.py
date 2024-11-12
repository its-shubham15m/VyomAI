from qrcode.image.styledpil import StyledPilImage
import qrcode.image.styles.colormasks as masks
import qrcode.image.svg
import streamlit as st
import qrcode
from models.res.utils import hex_to_rgb
from models.res.utils import setup_qrcode
from models.res.config import mods_dict


def QR():
    if not 'img' in st.session_state:
        st.session_state.img = ''

    st.header('QRCode Generator', divider='rainbow')

    c1, c2 = st.columns(gap='medium', spec=2)

    with c1:
        text = st.text_input("Enter you link", key='content')

        c11, c12 = st.columns(2)

        with c11:
            color = st.color_picker("Pick a color", "#000000", key='color_picker')
        with c12:

            st.selectbox(
                "Select a format", ['png', 'svg'],
                key='format',
            )

            format = st.session_state.format

        c13, c14 = st.columns(2)

        with c13:

            if format == 'svg':

                st.selectbox(
                    "Select resolution", ['256 x 256', '512 x 512', '1024 x 1024'],
                    key=f'resolution_{format}',
                    disabled=True,
                )

            else:

                st.selectbox(
                    "Select resolution", ['256 x 256', '512 x 512', '1024 x 1024'],
                    key=f'resolution_{format}',
                )

        with c14:

            modStyle = st.selectbox(
                "Select module type",
                options=list(mods_dict[format].keys()),
                key='module_style',
            )

        c15, c16, c17 = st.columns(3)

        with c16:
            with st.empty():
                if st.button("I'm ready!", type='primary'):
                    resolution = st.session_state[f'resolution_{format}']
                    setup_qrcode(text, mods_dict[format], format, color, resolution, modStyle)

    with c2:
        qr = qrcode.QRCode(
            box_size=8,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            mask_pattern=0,
        )

        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            color_mask=masks.SolidFillColorMask(
                back_color=(255, 255, 255),
                front_color=hex_to_rgb(color),
            ),
            module_drawer=mods_dict['png'][modStyle],
        )

        img_st = img.convert("RGB").resize((300, 300))
        st.image(img_st)