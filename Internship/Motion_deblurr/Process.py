from psf_generation import create_gaussian_psf, create_gaussian_psf_3d, bas_psf
import cv2
import matplotlib.pyplot as plt
import  numpy as np
from scipy import signal
from skimage import restoration, color

"""
This script is about discovering the steps and tools of the deblurring process.

Default "Controlled process" and working of the script:

    First we take a clear image (preferably taken by a camera) then blurr it via convolution using a known PSF. 
    Then since we have used a known PSF, we can deduce the PSF to use at the deconvolution process.
    But deconvoluting an image with a PSF amplifies it's noise. Because a PSF's high frequency components go to 0 inherently which makes "dividing" by it makes
    image's high frequencies get amplified which in return causes noise.
    Thus we utilize an denoising filter. 
    Using an filter makes the image lose its brightness; thus, we also have to make some adjustments about it. 

    At the end we should see a clear image similar to the inputed one.

Due to this process, we can confirm that deconvolution and denoising tools do work. And play with them to see how they react to different PSF's, images, parametrization etc.
We can also understand what kind of blurring happens when we use different kind of PSF's. It also is useful to understand the relationship between the PSF that is used
in convolution and deconvolution. 
This is important since we can not know what is the PSF of an already blurred image. 
Thus can not deduce the characteristic of the PSF to be used at the deconvolution without further advanced techniques to estimate the PSF of the blurred image.
But without confirming that these tools do work and what kind of configuration should have been done (such as need to filter deconvoluted images 
or amplify their brightness after filtering, type conversions, syntax issues etc.) to make them work, we can not understand that those advanced techniques were successfull
or not at estimating the PSF. This is also about not adding another problematic parameter into the problem so since it is almost guaranteed that there will be either a
problem or issue, it is important that we can single out the problems. If we straight up started with the already blurred photograph then in every problem ve face, we would 
have had to consider whether if have used the right PSF or not alongside the actual problem we have just faced. 

The next step from here forward is to build a PSF estimation script and test it via this script. The estimated PSF should be inputed here for deconvolution after 
required revisions. For and idea, we may try to estimate the PSF of the image that was blurred by this script with a known PSF at the first place.

        ######################## ABOUT the enabling and disabling variables: rgb, nat, display_mode, mode  ##################################
    
    We have rgb and nat variables at the first part. rgb variable is about whether we will process the image in greyscale or colored so the output is grey or colored.
   
    If the rgb = 1, 
                    it means a colored output is aimed and vice versa. In general, working with a greyscale image is easier and faster. It is wise to adjust the process that
    was successful for greyscale to rgb later on. This can be achieved by seperating the layers of the colored image to treat it as 2D array as this was also the case for
    the greyscale images.

    If the nat = 1, 
                    then we are skipping the convolution step to work with a already blurred "natural" image and move directly to deconvolution step. If nat = 0, the 
    default "controlled process" is to be run with a clear image.
    
    If the display_mode = 0, 
                            every display() function is not to be run, it is wise to continue to work on the script in this manner, since a lot of parameters or other
    stuff tested, we may just want to see a single part/stage of the code without dealing with multiple displays everytime. This also saves us from deleting display()
    and rewriting (commenting/decommenting) it all the time. display_mode = 1 enables the display() functions.
    
    mode 
        variable is about the deconvolution method to be chosen. Simply follow the instructions at the related part. Note that until now, it was only possible for
    mode = 2 which corresponds to unsupervised_wiener() method to complete the process and reach a cleared image at the end.
    
    Default values:
        rgb = 0
        nat = 0
        display_mode = 1
        mode = 2
        
        ######################### ABOUT the enabling and disabling variables  #######################################

        ############################## PSF values ##################################

For a successful run with default values for image = "clear_img3.jfif", you may use the following PSF values:

Convolution PSF:

    psf_size_x = 40 
    psf_size_y = 40 
    
    psf_sigma_x = 4.00  
    psf_sigma_y = 4.00
    
    psf_center_x = 0.0  
    psf_center_y = 0.0  
    
Deconvolution PSF:

    psf_size_x = 40 
    psf_size_y = 40 
    
    psf_sigma_x = 20.00  
    psf_sigma_y = 20.00
    
    psf_center_x = 0.0  
    psf_center_y = 0.0 
    
        ############################ PSF values #############################

"""

def display(image,result,title,mode=0): #to display original image and it's processed version
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle(title, fontsize=16)
    # Plot the initial image

    if mode == 0 or mode == 1:
        image_uint8 = np.clip(image, 0, 255).astype(np.uint8)
    elif mode == 2:
        image_uint8 = image[0].astype(np.uint8)

    axs[0].imshow(cv2.cvtColor(image_uint8, cv2.COLOR_BGR2RGB))
    axs[0].set_title("Initial Image")
    axs[0].axis("off")

    if mode == 0 or mode == 1:
        result_uint8 = np.clip(result, 0, 255).astype(np.uint8)
    elif mode == 2:
        result_uint8 = result[0].astype(np.uint8)

    # Plot the processed image
    axs[1].imshow(cv2.cvtColor(result_uint8, cv2.COLOR_BGR2RGB))
    axs[1].set_title("Processed Image")
    axs[1].axis("off")
    plt.tight_layout()
    #plt.colorbar()
    def on_key(event):
        plt.close(fig)

    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()


def calculate_snr(original_image, noisy_image):
    # Calculate the mean squared error (MSE) between the original and noisy images
    mse = np.mean((original_image - noisy_image) ** 2)

    # Calculate the power of the original image
    original_power = np.mean(original_image ** 2)

    # Calculate the SNR in decibels (dB)
    snr_db = 10 * np.log10(original_power / mse)

    return snr_db

### Read image
img = cv2.imread("clear_img3.jfif",cv2.IMREAD_GRAYSCALE)

img_rgb = cv2.imread("clear_img3.jfif")

brightimg = cv2.convertScaleAbs(img_rgb, alpha= 3, beta= 10)

nat_img = cv2.imread("blurred_img1.jfif",cv2.IMREAD_GRAYSCALE)

        ############ RGB & NAT ##############
rgb = 0
nat = 0
        ############ RGB & NAT ##############

if(rgb):
    image = img_rgb
    print("RGB 1")
else:
    image = img
    print("GREY 1")

################# Determine the parameters
height, width = img.shape

psf_size_x = 40 #width  #2048 # Size of the PSF in the X dimension
psf_size_y = 40 #height #1536 # Size of the PSF in the Y dimension

psf_sigma_x = 5.00  # Standard deviation of the Gaussian distribution in the X dimension
psf_sigma_y = 01.00  # Standard deviation of the Gaussian distribution in the Y dimension

psf_center_x = 5.0  # X coordinate of the PSF center
psf_center_y = 0.0  # Y coordinate of the PSF center

#####

# Deconvo PSF
psf_size_x_D = 40 #width  #2048 # Size of the PSF in the X dimension
psf_size_y_D = 40 #height #1536 # Size of the PSF in the Y dimension

psf_sigma_x_D = 30.00  # Standard deviation of the Gaussian distribution in the X dimension
psf_sigma_y_D = 01.15  # Standard deviation of the Gaussian distribution in the Y dimension

psf_center_x_D = -85.0  # X coordinate of the PSF center
psf_center_y_D = -10.0  # Y coordinate of the PSF center

###################

# Create the Gaussian PSF with shifted center
gaussian_psf = create_gaussian_psf(psf_size_x, psf_size_y, psf_sigma_x, psf_sigma_y, psf_center_x, psf_center_y)
# for rgb we need 3d psf
gaussian_psf_3d = create_gaussian_psf_3d(psf_size_x, psf_size_y, psf_sigma_x, psf_sigma_y, psf_center_x, psf_center_y)

# Gaussian PSF to use in deconvolution process
gaussian_psf_D = create_gaussian_psf(psf_size_x_D, psf_size_y_D, psf_sigma_x_D, psf_sigma_y_D, psf_center_x_D, psf_center_y_D)
# deconvo. psf for rgb
gaussian_psf_3d_D = create_gaussian_psf_3d(psf_size_x_D, psf_size_y_D, psf_sigma_x_D, psf_sigma_y_D, psf_center_x_D, psf_center_y_D)

plt.imshow(gaussian_psf_D, cmap='hot', interpolation='nearest') # For 3D: gaussian_psf_3d[:, :, 1]
plt.colorbar()
plt.show()

# Convolute image and kernel to acquire blurred image
blurred_img = cv2.filter2D(img, -1, gaussian_psf)
blurred_img = blurred_img.astype(np.float64)
# RGB:
blurred_img_rgb = cv2.filter2D(img_rgb, -1, gaussian_psf_3d)
blurred_img_rgb = blurred_img_rgb.astype(np.float64)

if(rgb):
    blurred_image = blurred_img_rgb
    print("RGB 2")
else:
    blurred_image = blurred_img
    print("GREY 2")

# Display original and blurred image side by side-
##################### DISPLAY MODE
display_mode = 1 # Enable display-> 1, Disable display-> 0

if(display_mode):
    if(nat):
        print("NAT 2")
    else:
        display(image, blurred_image, "Sharp2Blurred")

# To pick which deconvolution method has been used
####################### DECONVO MODE
mode = 2 # RL->0, W->1, UW->2

if(mode == 0):
    # Deconvolution of blurred image and PSF by Richardson-Lucy Deconvolution
    sharpened_img = restoration.richardson_lucy(blurred_image, gaussian_psf, 10)
    # Display blurred and sharpened image side by side
    if(display_mode):
        display(blurred_image, sharpened_img, "Blurred2Sharp")

elif(mode == 1):
    # Deconvolution of blurred image and PSF by Wiener Deconvolution
    sharpened_img = restoration.wiener(blurred_image, gaussian_psf,0.1)

    # Display blurred and sharpened image side by side
    if(display_mode):
        display(blurred_image, sharpened_img, "Blurred2Sharp")

elif(mode == 2):
    # Deconvolution of blurred image and PSF by Unsupervised Wiener Deconvolution

            ############################### RGB TRIAL ##############################
    if(rgb):
        print("RGB 3")
        SNR_rgb = calculate_snr(blurred_image, image)
        revised_psf_3d = gaussian_psf_3d_D / (np.abs(gaussian_psf_3d_D)**2 + 1/100) # Wiener deconvolution formula
        psf_lay1 = revised_psf_3d[:, :, 0]
        psf_lay2 = revised_psf_3d[:, :, 1]
        psf_lay3 = revised_psf_3d[:, :, 2]


        img_lay1 = image[:, :, 0]
        img_lay2 = image[:, :, 1]
        img_lay3 = image[:, :, 2]

        sharpened_img_rgb_lay1, estimated_psf_3d_lay1 = restoration.unsupervised_wiener(img_lay1, psf_lay1)
        sharpened_img_rgb_lay2, estimated_psf_3d_lay2 = restoration.unsupervised_wiener(img_lay1, psf_lay2)
        sharpened_img_rgb_lay3, estimated_psf_3d_lay3 = restoration.unsupervised_wiener(img_lay1, psf_lay3)

        sharpened_img_rgb = np.dstack((sharpened_img_rgb_lay1, sharpened_img_rgb_lay2, sharpened_img_rgb_lay3))
                ############################### RGB TRIAL ##############################
    else:
        print("GREY 3")

        SNR = calculate_snr(blurred_image, image)
        revised_psf = gaussian_psf_D / (np.abs(gaussian_psf_D)**2 + 1/1000)
        if(nat):
            print("NAT 2")
            sharpened_nat_img, estimated_psf_nat = restoration.unsupervised_wiener(nat_img, revised_psf)
        else:
            sharpened_img, estimated_psf = restoration.unsupervised_wiener(blurred_image, revised_psf)

    if(rgb):
        sharpened_image = sharpened_img_rgb
        print("RGB 4")
    else:
        #sharpened_image = sharpened_img
        if(nat):
            print("NAT 3")
            sharpened_image = cv2.convertScaleAbs(restoration.denoise_tv_chambolle(sharpened_nat_img, weight = 0.1, channel_axis= False), alpha= 1000, beta= 10) # weight 0.1 at best
            blurred_image = nat_img
        else:
            #filtered_image = restoration.denoise_tv_chambolle(sharpened_img, weight=0.1, channel_axis=False)
            sharpened_image = cv2.convertScaleAbs(restoration.denoise_tv_chambolle(sharpened_img, weight=0.1, channel_axis=False), alpha=1000,beta=10)  # weight 0.1 at best

        print("GREY 4")

    display(blurred_image,sharpened_image,"blur2sharp")


    #sharpened_filtered_img = restoration.denoise_tv_chambolle(sharpened_img, weight = 0.1, channel_axis= False)
    #cv2.namedWindow("sharpened", cv2.WINDOW_NORMAL)
    #cv2.imshow("sharpened", cv2.convertScaleAbs(sharpened_img, alpha=1000,beta=10))
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    # Display blurred and sharpened image side by side
    #if(display_mode):
        #display(blurred_img, sharpened_filtered_img, "Blurred2Sharp")
















