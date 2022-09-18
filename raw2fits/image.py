from debayer import *
import rawpy
import exifread
from astropy.io import fits
from datetime import datetime, timezone

class Image():
    def __init__(self, path, debayer_method="VNG"):
        # Check file existence
        if not os.path.exists(path):
            raise FileNotFoundError(f"File {path} does not exist.")
        self.file_extension = os.path.splitext(path)[1]
        # Initialize attributes
        self.path = path
        self.debayer_method = debayer_method
        print("Reading image...")
        self.bayer_image = self._get_bayer_image(path)
        self.image_size = self.bayer_image.shape
        print(f"Debayering ({self.debayer_method}, {self.image_size[0]} x {self.image_size[1]})...")
        self.debayer_image = self._get_debayer_image(path, debayer_method)
        self.exif = self._get_exif(path)
        pass

    def __repr__(self):
        return f"Image(path={self.path}, debayer_method={self.debayer_method})"\
        
    def __str__(self):
        return f"Image(path={self.path}, debayer_method={self.debayer_method})"
    
    def _get_bayer_image(self, path):
        return rawpy.imread(path).raw_image_visible

    def _get_debayer_image(self, path, debayer_method):
        return debayer(path, method=debayer_method)

    def _get_exif(self, path):
        return exifread.process_file(open(path, 'rb')) 

    def save_fits(self, image_type, path=None):
        """
        Save the image as a FITS file.
        image_type: "LIGHT", "DARK", "FLAT", "BIAS"
        path: path to save the file to. If None, save to the same directory as the image.
        """
        hdu = fits.PrimaryHDU(self.debayer_image)
        hdul = fits.HDUList([hdu])

        # Add EXIF data to FITS header
        header = hdul[0].header

        header.comments["NAXIS"] = "Dimensionality"
        header.comments["EXTEND"] = "Extensions are permitted"

        if image_type in ["LIGHT", "DARK", "FLAT", "BIAS"]:
            header["IMAGETYP"] = image_type
            header.comments["IMAGETYP"]= "Type of exposure"
            
        else:
            raise ValueError(f"Invalid image type: {image_type}")

        if "EXIF ExposureTime" in self.exif:
            if "/" in str(self.exif["EXIF ExposureTime"]):
                exposure_time = float(str(self.exif["EXIF ExposureTime"]).split("/")[0])/float(str(self.exif["EXIF ExposureTime"]).split("/")[1])
            else:
                exposure_time = float(str(self.exif["EXIF ExposureTime"]))
            header["EXPSURE"] = exposure_time
            header["EXPTIME"] = exposure_time
            header.comments["EXPSURE"] = "[s] Exposure duration"
            header.comments["EXPTIME"]= "[s] Exposure duration"

        if "Image DateTime" in self.exif:
            dt_str = self.exif["Image DateTime"].printable # datetime string
            if "EXIF OffsetTime" in self.exif: # timezone
                tz_str = self.exif["EXIF OffsetTime"].printable # timezone string
                dt = datetime.strptime(dt_str+tz_str, "%Y:%m:%d %H:%M:%S%z") # datetime object
                dt_utc = dt.astimezone(timezone.utc) # datetime object in UTC
                header["DATE-LOC"] = dt.replace(tzinfo=None).isoformat()
                header["DATE-OBS"] = dt_utc.replace(tzinfo=None).isoformat()
                header.comments["DATE-LOC"] = "Time of observation (local)"
                header.comments["DATE-OBS"] = "Time of observation (UTC)"
            else:
                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S") # datetime object
                header["DATE-LOC"] = dt.replace(tzinfo=None).isoformat()
                header["DATE-OBS"] = dt.replace(tzinfo=None).isoformat()
                header.comments["DATE-LOC"] = "Time of observation (local)"
                header.comments["DATE-OBS"] = "Time of observation (local)"

        header["XBINNING"] = 1
        header["YBINNING"] = 1
        header.comments["XBINNING"] = "X axis binning factor"
        header.comments["YBINNING"] = "Y axis binning factor"

        if "EXIF ISOSpeedRatings" in self.exif:
            header["GAIN"] = int(self.exif["EXIF ISOSpeedRatings"].printable)
            header.comments["GAIN"] = "Sensor gain (ISO)"

        if "EXIF FocalPlaneXResolution" in self.exif and "EXIF FocalPlaneYResolution" in self.exif:
            xv1, xv2 = self.exif["EXIF FocalPlaneXResolution"].printable.split("/")
            yv1, yv2 = self.exif["EXIF FocalPlaneYResolution"].printable.split("/")
            dpi_x = float(xv1)/float(xv2)
            dpi_y = float(yv1)/float(yv2)
            sensor_size_x = self.image_size[1] / dpi_x * 25.4 # mm
            sensor_size_y = self.image_size[0] / dpi_y * 25.4 # mm
            pixel_scale_x = sensor_size_x / self.image_size[1] * 1000 # um
            pixel_scale_y = sensor_size_y / self.image_size[0] * 1000 # um
            header["XPIXSZ"] = pixel_scale_x
            header["YPIXSZ"] = pixel_scale_y
            header.comments["XPIXSZ"] = "[um] Pixel X axis size"
            header.comments["YPIXSZ"] = "[um] Pixel Y axis size"

        if "Image Model" in self.exif:
            header["INSTRUME"] = self.exif["Image Model"].printable
            header.comments["INSTRUME"] = "Imaging instrument name"

        if "EXIF LensModel" in self.exif:
            header["TELESCOP"] = self.exif["EXIF LensModel"].printable
            header.comments["TELESCOP"] = "Name of telescope"
        
        if "EXIF FocalLength" in self.exif:
            if "/" in str(self.exif["EXIF FocalLength"]):
                focal_length = float(str(self.exif["EXIF FocalLength"]).split("/")[0])/float(str(self.exif["EXIF FocalLength"]).split("/")[1])
            else:
                focal_length = float(str(self.exif["EXIF FocalLength"]))

            header["FOCALLEN"] = focal_length
            header.comments["FOCALLEN"] = "[mm] Focal length"

        if "Image Artist" in self.exif:
            header["OBSERVER"] = self.exif["Image Artist"].printable
            header.comments["OBSERVER"] = "Observer name"

        # get version from __init__.py
        with open(os.path.join(os.path.dirname(__file__), "__init__.py")) as f:
            for line in f:
                if line.startswith("__version__"):
                    version = line.split("=")[1].strip().strip('"')
                    header["SWCREATE"] = f"raw2fits v{version}"
                    header.comments["SWCREATE"] = "Software used to create this file"
                    break
                
        if path is None:
            path = self.path.replace(self.file_extension, ".fits")
        else:
            path = os.path.join(path, self.path.split("/")[-1].replace(self.file_extension, ".fits"))

        print(f"Saving FITS file to {path}")     
        hdul.writeto(path, overwrite=True)
        pass

