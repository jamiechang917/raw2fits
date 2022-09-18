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
where `debayer_method` can be one of the following: "VNG", "Bilinear". We recommend using "VNG" for better results, this is also the default method used by PixInsight and this package. `raw2fits` supports 16-bit VNG debayer method, which is not supported by OpenCV yet.

### Comparsion between different debayer methods
  
The following images are the result of converting a raw image to a fits file using different debayer methods.

|     Debayer Method      |                             Image                             |
| :---------------------: | :-----------------------------------------------------------: |
|      **Bilinear**       |   <img width=250px  src=tests/debayer_examples/full/BL.jpg>   |
|         **VNG**         |  <img width=250px  src=tests/debayer_examples/full/VNG.jpg>   |
| **VNG (by Pixinsight)** | <img width=250px  src=tests/debayer_examples/full/VNG_PI.jpg> |

---

|     Debayer Method      |                              Image                               |
| :---------------------: | :--------------------------------------------------------------: |
|      **Bilinear**       |   <img width=250px  src=tests/debayer_examples/cropped/BL.png>   |
|         **VNG**         |  <img width=250px  src=tests/debayer_examples/cropped/VNG.png>   |
| **VNG (by Pixinsight)** | <img width=250px  src=tests/debayer_examples/cropped/VNG_PI.png> |
---

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Acknowledgements
This extraction of the bayer image is based on the [rawpy](https://github.com/letmaik/rawpy).