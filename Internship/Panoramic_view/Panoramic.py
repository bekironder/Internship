import numpy as np
import cv2
import os
import matplotlib.pyplot as plt

def warpImages(img1, img2, H):
    rows1, cols1 = img1.shape[:2]
    rows2, cols2 = img2.shape[:2]

    list_of_points_1 = np.float32([
        [0, 0],
        [0, rows1],
        [cols1, rows1],
        [cols1, 0]
    ])
    list_of_points_1 = list_of_points_1.reshape(-1, 1, 2)

    temp_points = np.float32([
        [0, 0],
        [0, rows2],
        [cols2, rows2],
        [cols2, 0]
    ])
    temp_points = temp_points.reshape(-1, 1, 2)

    list_of_points_2 = cv2.perspectiveTransform(temp_points, H)

    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)

    translation_dist = [-x_min, -y_min]

    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

    output_img = cv2.warpPerspective(img2, H_translation.dot(H), (x_max - x_min, y_max - y_min))
    output_img[translation_dist[1]:rows1 + translation_dist[1], translation_dist[0]:cols1 + translation_dist[0]] = img1

    return output_img

def warp(img1, img2, min_match_count=10):
    sift = cv2.SIFT_create()

    keypoints1, descriptors1 = sift.detectAndCompute(img1, None)
    keypoints2, descriptors2 = sift.detectAndCompute(img2, None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(descriptors1, descriptors2, k=2)

    good_matches = []
    for m1, m2 in matches:
        if m1.distance < 0.7 * m2.distance:
            good_matches.append(m1)

    if len(good_matches) > min_match_count:
        src_pts = np.float32([keypoints1[good_match.queryIdx].pt for good_match in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints2[good_match.trainIdx].pt for good_match in good_matches]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        result = warpImages(img2, img1, M)
        return result
    else:
        print("We don't have enough number of matches between the two images.")
        print("Found only " + str(len(good_matches)) + " matches.")
        print("We need at least " + str(min_match_count) + " matches.")

dim = (1024, 768)
left = cv2.imread('pan1.jfif', cv2.IMREAD_COLOR)
left = cv2.resize(left, dim, interpolation=cv2.INTER_AREA)

right = cv2.imread('pan2.jfif', cv2.IMREAD_COLOR)
right = cv2.resize(right, dim, interpolation=cv2.INTER_AREA)

pano = warp(left, right)

plt.imshow(pano[..., ::-1])
plt.title('Stitched Panoramic Image')
plt.xticks([]), plt.yticks([])  # Hide tick values on X and Y axis
plt.show()


