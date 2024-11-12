import qrcode.image.styles.moduledrawers.pil as mods
from qrcode.image.styles.moduledrawers import svg as svg_drawers


mods_dict = {
    'png': {

        'Square': mods.SquareModuleDrawer(),
        'Grapped': mods.GappedSquareModuleDrawer(),
        'Circle': mods.CircleModuleDrawer(),
        'Rounded': mods.RoundedModuleDrawer(),
        'Vertical': mods.VerticalBarsDrawer(),
        'Horizontal': mods.HorizontalBarsDrawer(),
    },

    'svg': {

        'Square': svg_drawers.SvgPathSquareDrawer(),
        'Circle': svg_drawers.SvgPathCircleDrawer(),
    }
}