import  cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import restoration
from skimage.measure import centroid
from PIL import Image, ImageFilter
from tifffile import imread
"""
PSF's are generated here to be used in deconvolution step

import psf, bas_psf or gaussian_psf (or create_gaussian_psf() & create_gaussian_psf_3d()) from here
"""

#################################################################################### Manually generated very basic PSF
psf_size = (877, 1316)  # Adjust the size as needed

# Define the motion blur direction (horizontal blur in this case)
blur_length = 10 # Adjust the length as needed
blur_width = 1
bas_psf = np.zeros(psf_size)
mid_shift = -50
for i in range(blur_width):
    #psf[int((psf_size[0]-1)/2)+i, int((psf_size[1]-1)/2-blur_length/2):int((psf_size[1]-1)/2+blur_length/2+1)] = 1/blur_length
    bas_psf[int((psf_size[0] - 1) / 2) + i, int((psf_size[1] - 1) / 2 - blur_length / 2 + mid_shift):int((psf_size[1] - 1) / 2 + blur_length / 2 + 1 + mid_shift)] = 1 / blur_length
bas_psf = np.roll(bas_psf, 00, axis=1)
###################################################################################



##Display bas_psf
#plt.imshow(bas_psf)
#plt.show()





#############################################################       GAUSSIAN PSF   #####################
import numpy as np
import matplotlib.pyplot as plt


def create_gaussian_psf(size_x, size_y, sigma_x, sigma_y, center_x, center_y):
    # Create a grid of coordinates
    x = np.linspace(-size_x/2, size_x/2, size_x)
    y = np.linspace(-size_y/2, size_y/2, size_y)
    xx, yy = np.meshgrid(x, y)

    # Shift the coordinates
    shifted_xx = xx - center_x
    shifted_yy = yy - center_y

    # Create a Gaussian distribution centered at the specified coordinates
    psf = np.exp(-(shifted_xx**2 / (2 * sigma_x**2) + shifted_yy**2 / (2 * sigma_y**2)))

    # Normalize the PSF to have a total sum of 1
    psf /= np.sum(psf)

    return psf

def create_gaussian_psf_3d(size_x, size_y, sigma_x, sigma_y, center_x, center_y, depth = 3):
    # Create a grid of coordinates
    x = np.linspace(-size_x/2, size_x/2, size_x)
    y = np.linspace(-size_y/2, size_y/2, size_y)
    xx, yy = np.meshgrid(x, y)

    # Shift the coordinates
    shifted_xx = xx - center_x
    shifted_yy = yy - center_y

    # Create a Gaussian distribution centered at the specified coordinates
    psf = np.exp(-(shifted_xx**2 / (2 * sigma_x**2) + shifted_yy**2 / (2 * sigma_y**2)))

    # Normalize the PSF to have a total sum of 1
    psf /= np.sum(psf)

    # Create a 3D array with the same PSF in all layers
    psf_3d = np.tile(psf[:, :, np.newaxis], depth)

    return psf_3d

# Parameters
psf_size_x = 40 #2048  # Size of the PSF in the X dimension
psf_size_y = 40 #1536  # Size of the PSF in the Y dimension

psf_sigma_x = 30.0 #100.0  # Standard deviation of the Gaussian distribution in the X dimension
psf_sigma_y = 2.15 #2.0  # Standard deviation of the Gaussian distribution in the Y dimension

psf_center_x = 20.0 #100.0  # X coordinate of the PSF center
psf_center_y = 0.0 #0.0  # Y coordinate of the PSF center

# Create the Gaussian PSF with shifted center
gaussian_psf = create_gaussian_psf(psf_size_x, psf_size_y, psf_sigma_x, psf_sigma_y, psf_center_x, psf_center_y)

gaussian_psf_3d = create_gaussian_psf_3d(psf_size_x, psf_size_y, psf_sigma_x, psf_sigma_y, psf_center_x, psf_center_y)

# Display the PSF as an image
plt.imshow(gaussian_psf, cmap='hot', interpolation='nearest') # For 3D: gaussian_psf_3d[:, :, 1]
plt.colorbar()
plt.show()

###########################################################################################################


