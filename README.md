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


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Acknowledgements
This extraction of the bayer image is based on the [rawpy](https://github.com/letmaik/rawpy).