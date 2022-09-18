import os
import numpy as np
import numba as nb
from numba_progress import ProgressBar
import cv2
import rawpy


def _debayer_VNG(bayer_img, color_index_map, color_desc):
    """Debayer a Bayer image using VNG interpolation.

    Parameters
    ----------
    bayer_img : ndarray
        Input Bayer image.
    color_index_map : ndarray
        Color index map.
    color_desc : dict
        Color description.

    Returns
    -------
    output : ndarray
        Output image.

    """
    # OpenCV's VNG interpolation is designed for 8-bit image, so we write the algorithm ourselves.
    # To see VNG interpolation in action, see https://ui.adsabs.harvard.edu/abs/1999SPIE.3650...36C/abstract
    # color_index_map is a 2D array of the same size as bayer_img, where each element is an integer from 0 to 3
    # indicating the color of the corresponding pixel in bayer_img.
    # color_desc is a list of 4 strings, each string is the name of the color corresponding to the index in color_index_map.
    # For example, if color_index_map[0, 0] = 0, then color_desc[0] is the name of the color of the pixel at (0, 0).
    # The order of the colors in color_desc is the same as the order of the colors in the Bayer pattern.
    # For example, if the Bayer pattern is RGGB, then color_desc[0] is "R", color_desc[1] is "G", color_desc[2] is "G", and color_desc[3] is "B".
    # Return a 3D array of the same size as bayer_img, where the first dimension is the color channel (red, green, blue).

    bayer_img_extended = np.pad(bayer_img, ((2, 2), (2, 2)), mode="edge").astype(np.float64) # Extend the image by 2 pixels on each side for VNG interpolation
    color_index_map_extended = np.pad(color_index_map, ((2, 2), (2, 2)), mode="edge")      # Extend the color index map by 2 pixels on each side for VNG interpolation
    color_desc_numba = nb.typed.List(color_desc) # Convert color_desc to a numba typed list for use in the numba function
    output = np.zeros((3, bayer_img.shape[0], bayer_img.shape[1]), dtype=np.float64) # Output image

    @nb.njit(parallel=False, fastmath=True)
    def interpolation(I, C, color_desc, output, progress_proxy):
        for i in nb.prange(2, I.shape[0] - 2):
            for j in nb.prange(2, I.shape[1] - 2):
                if color_desc[C[i, j]] == "G":
                    # Temporary variables
                    g1 , b1 , g2 , b2 , g3  = I[i-2, j-2:j+3]
                    r1 , g4 , r2 , g5 , r3  = I[i-1, j-2:j+3]
                    g6 , b3 , g7 , b4 , g8  = I[i  , j-2:j+3]
                    r4 , g9 , r5 , g10, r6  = I[i+1, j-2:j+3]
                    g11, b5 , g12, b6 , g13 = I[i+2, j-2:j+3]
                    # Gradient calculation
                    grad_N = abs(r2-r5) + abs(g2-g7) + abs(g4-g9)/2 + abs(g5-g10)/2 + abs(b1-b3)/2 + abs(b2-b4)/2
                    grad_E = abs(b4-b3) + abs(g8-g7) + abs(g5-g4)/2 + abs(g10-g9)/2 + abs(r3-r2)/2 + abs(r6-r5)/2
                    grad_S = abs(r5-r2) + abs(g12-g7) + abs(g9-g4)/2 + abs(g10-g5)/2 + abs(b5-b3)/2 + abs(b6-b4)/2
                    grad_W = abs(b3-b4) + abs(g6-g7) + abs(g4-g5)/2 + abs(g9-g10)/2 + abs(r1-r2)/2 + abs(r4-r5)/2
                    grad_NE = abs(g5-g9) + abs(g3-g7) + abs(b2-b3) + abs(r3-r5)
                    grad_SE = abs(g10-g4) + abs(g13-g7) + abs(b6-b3) + abs(r6-r2)
                    grad_NW = abs(g4-g10) + abs(g1-g7) + abs(b1-b4) + abs(r1-r5)
                    grad_SW = abs(g9-g5) + abs(g11-g7) + abs(b5-b4) + abs(r4-r2)
                    # Threshold calculation
                    MAX = max(grad_N, grad_E, grad_S, grad_W, grad_NE, grad_SE, grad_NW, grad_SW)
                    MIN = min(grad_N, grad_E, grad_S, grad_W, grad_NE, grad_SE, grad_NW, grad_SW)
                    threshold = 1.5*MIN + 0.5*(MAX-MIN)
                    cnt = 0
                    sum_R, sum_G, sum_B = 0.0, 0.0, 0.0
                    if grad_N <= threshold:
                        cnt += 1
                        sum_R += r2
                        sum_G += (g2+g7)/2
                        sum_B += (b1+b2+b3+b4)/4
                    if grad_E <= threshold:
                        cnt += 1
                        sum_R += (r2+r3+r5+r6)/4
                        sum_G += (g8+g7)/2
                        sum_B += b4
                    if grad_S <= threshold:
                        cnt += 1
                        sum_R += r5
                        sum_G += (g12+g7)/2
                        sum_B += (b3+b4+b5+b6)/4
                    if grad_W <= threshold:
                        cnt += 1
                        sum_R += (r1+r2+r4+r5)/4
                        sum_G += (g6+g7)/2
                        sum_B += b3
                    if grad_NE <= threshold:
                        cnt += 1
                        sum_R += (r2+r3)/2
                        sum_G += g5
                        sum_B += (b2+b4)/2
                    if grad_SE <= threshold:
                        cnt += 1
                        sum_R += (r5+r6)/2
                        sum_G += g10
                        sum_B += (b4+b6)/2
                    if grad_NW <= threshold:
                        cnt += 1
                        sum_R += (r1+r2)/2
                        sum_G += g4
                        sum_B += (b1+b3)/2
                    if grad_SW <= threshold:
                        cnt += 1
                        sum_R += (r4+r5)/2
                        sum_G += g9
                        sum_B += (b3+b5)/2
                    # Blue Row
                    if i%2 == 1:
                        output[0, i-2, j-2] = g7 + (sum_R - sum_G)/cnt
                        output[1, i-2, j-2] = g7
                        output[2, i-2, j-2] = g7 + (sum_B - sum_G)/cnt
                    # Red Row
                    else:   
                        output[0, i-2, j-2] = g7 + (sum_B - sum_G)/cnt
                        output[1, i-2, j-2] = g7
                        output[2, i-2, j-2] = g7 + (sum_R - sum_G)/cnt
                elif color_desc[C[i, j]] == "R" or color_desc[C[i, j]] == "B":
                    # Temporary variables
                    r1 , g1 , r2 , g2 , r3  = I[i-2, j-2:j+3]
                    g3 , b1 , g4 , b2 , g5  = I[i-1, j-2:j+3]
                    r4 , g6 , r5 , g7 , r6  = I[i  , j-2:j+3]
                    g8 , b3 , g9 , b4 , g10 = I[i+1, j-2:j+3]
                    r7 , g11, r8 , g12, r9  = I[i+2, j-2:j+3]
                    # Gradient calculation
                    grad_N = abs(g4-g9) + abs(r2-r5) + abs(b1-b3)/2 + abs(b2-b4)/2 + abs(g1-g6)/2 + abs(g2-g7)/2
                    grad_E = abs(g7-g6) + abs(r6-r5) + abs(b2-b1)/2 + abs(b4-b3)/2 + abs(g5-g4)/2 + abs(g10-g9)/2
                    grad_S = abs(g9-g4) + abs(r8-r5) + abs(b3-b1)/2 + abs(b4-b2)/2 + abs(g11-g6)/2 + abs(g12-g7)/2
                    grad_W = abs(g6-g7) + abs(r4-r5) + abs(b1-b2)/2 + abs(b3-b4)/2 + abs(g3-g4)/2 + abs(g8-g9)/2
                    grad_NE = abs(b2-b3) + abs(r3-r5) + abs(g4-g6)/2 + abs(g7-g9)/2 + abs(g2-g4)/2 + abs(g5-g7)/2
                    grad_SE = abs(b4-b1) + abs(r9-r5) + abs(g7-g4)/2 + abs(g9-g6)/2 + abs(g10-g7)/2 + abs(g12-g9)/2
                    grad_NW = abs(b1-b4) + abs(r1-r5) + abs(g4-g7)/2 + abs(g6-g9)/2 + abs(g1-g4)/2 + abs(g3-g6)/2
                    grad_SW = abs(b3-b2) + abs(r7-r5) + abs(g6-g4)/2 + abs(g9-g7)/2 + abs(g8-g6)/2 + abs(g11-g9)/2
                    # Threshold calculation
                    MAX = max(grad_N, grad_E, grad_S, grad_W, grad_NE, grad_SE, grad_NW, grad_SW)
                    MIN = min(grad_N, grad_E, grad_S, grad_W, grad_NE, grad_SE, grad_NW, grad_SW)
                    threshold = 1.5*MIN + 0.5*(MAX-MIN)
                    cnt = 0
                    sum_R, sum_G, sum_B = 0.0, 0.0, 0.0
                    if grad_N <= threshold:
                        cnt += 1
                        sum_R += (r2+r5)/2
                        sum_G += g4
                        sum_B += (b1+b2)/2
                    if grad_E <= threshold:
                        cnt += 1
                        sum_R += (r6+r5)/2
                        sum_G += g7
                        sum_B += (b2+b4)/2
                    if grad_S <= threshold:
                        cnt += 1
                        sum_R += (r8+r5)/2
                        sum_G += g9
                        sum_B += (b3+b4)/2
                    if grad_W <= threshold:
                        cnt += 1
                        sum_R += (r4+r5)/2
                        sum_G += g6
                        sum_B += (b1+b3)/2
                    if grad_NE <= threshold:
                        cnt += 1
                        sum_R += (r3+r5)/2
                        sum_G += (g2+g4+g5+g7)/4
                        sum_B += b2
                    if grad_SE <= threshold:
                        cnt += 1
                        sum_R += (r9+r5)/2
                        sum_G += (g7+g9+g10+g12)/4
                        sum_B += b4
                    if grad_NW <= threshold:
                        cnt += 1
                        sum_R += (r1+r5)/2
                        sum_G += (g1+g3+g4+g6)/4
                        sum_B += b1
                    if grad_SW <= threshold:
                        cnt += 1
                        sum_R += (r7+r5)/2
                        sum_G += (g6+g8+g9+g11)/4
                        sum_B += b3

                    if color_desc[C[i, j]] == "R":
                        output[0, i-2, j-2] = r5
                        output[1, i-2, j-2] = r5 + (sum_G - sum_R)/cnt
                        output[2, i-2, j-2] = r5 + (sum_B - sum_R)/cnt
                    elif color_desc[C[i, j]] == "B":
                        output[0, i-2, j-2] = r5 + (sum_B - sum_R)/cnt
                        output[1, i-2, j-2] = r5 + (sum_G - sum_R)/cnt
                        output[2, i-2, j-2] = r5
                progress_proxy.update(1)
        return output
    
    with ProgressBar(total=(bayer_img_extended.shape[0] - 4)*(bayer_img_extended.shape[1] - 4)) as progress:
        output = interpolation(I=bayer_img_extended, C=color_index_map_extended, color_desc=color_desc_numba, output=output, progress_proxy=progress)
        output[output <= 0.0] = 0.0 # Clip negative values
        output[output >= 65535.0] = 65535.0 # Clip values above 65535
        return output.astype(np.uint16) # Convert to 16-bit unsigned integer

def _debayer_bilinear(bayer_img, color_desc):
    """Debayer a Bayer image using bilinear interpolation.

    Parameters
    ----------
    bayer_img : ndarray
        Input Bayer image.
    color_desc : dict
        Color description.

    Returns
    -------
    output : ndarray
        Output image.

    """
    # Create output image
    bayer_pattern = "".join(color_desc)
    if bayer_pattern == "RGGB" or bayer_pattern == "RGBG":
        output = cv2.cvtColor(bayer_img, cv2.COLOR_BayerBG2RGB) # Use OpenCV's debayering function
    elif bayer_pattern == "BGGR":
        output = cv2.cvtColor(bayer_img, cv2.COLOR_BayerRG2RGB) # Use OpenCV's debayering function
    elif bayer_pattern == "GRBG":
        output = cv2.cvtColor(bayer_img, cv2.COLOR_BayerGB2RGB)
    elif bayer_pattern == "GBRG":
        output = cv2.cvtColor(bayer_img, cv2.COLOR_BayerGR2RGB)
    else:
        raise ValueError(f"Bayer pattern {bayer_pattern} does not support.")

    return np.moveaxis(output, -1, 0) # Move color channel axis to the front
    
def debayer(path, method="VNG"):
    """Debayer a raw image using the specified method.
    Parameters
    ----------
    path : str
        Path to the raw image.
    method : str
        Debayering method to use. Must be one of "VNG" or "Bilinear".
    Returns
    -------
    output : ndarray
        The debayered image.
    """
    # Check file existence
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} does not exist.")


    # Read raw image
    with rawpy.imread(path) as raw:
        bayer_img = raw.raw_image_visible # Bayer image
        color_index_map = raw.raw_colors_visible # Color index map
        color_desc = [*raw.color_desc.decode()] # Color description

        # Debayer image
        if method == "VNG":
            return _debayer_VNG(bayer_img=bayer_img, color_index_map=color_index_map, color_desc=color_desc)
        elif method == "Bilinear":
            return _debayer_bilinear(bayer_img=bayer_img, color_desc=color_desc)
        else:
            raise ValueError("Invalid method. Must be one of 'VNG' or 'Bilinear'.")


