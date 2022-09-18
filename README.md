# raw2fits
A Python package to convert camera raw images to astronomical fits files.

## Installation
```bash
pip install raw2fits
```

## Usage

### To convert a raw image to a fits file.

```python
from raw2fits.image import Image
img = Image(path='path/to/raw/image', debayer_method="VNG")
img.save_fits(image_type="LIGHT", path='path/to/save/fits/image')
```
where `debayer_method` can be one of the following: "VNG", "Bilinear". We recommend using "VNG" for better results.

### Comparsion between different debayer methods
  
The following images are the result of converting a raw image to a fits file using different debayer methods.

<table align="center" style="border:1px solid white;margin-left:auto;margin-right:auto;margin-upper:auto;width: 80%;", border="1">
<caption style="caption-side:bottom">Full Image Comparsion</caption>
  <tr>
    <td style="text-align:center"> Bilinear</td>
    <td align="center"> <img src=tests/debayer_examples/full/BL.jpg></td>
  </tr>
  <tr>
    <td style="text-align:center"> VNG</td>
    <td align="center"> <img src=tests/debayer_examples/full/VNG.jpg></td>
  </tr>
  <tr>
    <td style="text-align:center"> VNG (by Pixinsight)</td>
    <td align="center"> <img src=tests/debayer_examples/full/VNG_PI.jpg></td>
  </tr>
</table>

---

<table align="center" style="border:1px solid white;margin-left:auto;margin-right:auto;margin-upper:auto;width: 80%;", border="1">
<caption style="caption-side:bottom">Cropped Image Comparsion</caption>
  <tr>
    <td align="center"> <img src=tests/debayer_examples/cropped/BL.png></td>
    <td align="center"> <img src=tests/debayer_examples/cropped/VNG.png></td>
    <td align="center"> <img src=tests/debayer_examples/cropped/VNG_PI.png></td>
   </tr>
   <tr>
   <td style="text-align:center"> Bilinear</td>
   <td style="text-align:center"> VNG</td>
   <td style="text-align:center"> VNG (by Pixinsight)</td>
   </tr>
</table>

---

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Acknowledgements
This extraction of the bayer image is based on the [rawpy](https://github.com/letmaik/rawpy).