"""Use locally installed fonts only; no font files are redistributed."""
from PIL import ImageFont
from pathlib import Path

def local_font(size: int, bold: bool=False):
    names=[
      '/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',
      '/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',
      'C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),
      'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
    ]
    for name in names:
        try: return ImageFont.truetype(name,size)
        except OSError: pass
    return ImageFont.load_default(size=size)
