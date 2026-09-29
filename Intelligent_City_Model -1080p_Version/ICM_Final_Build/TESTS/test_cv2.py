import cv2

img = cv2.imread("test.jpg")  # Usa cualquier imagen PNG o JPG
cv2.imshow("Test Image", img)
cv2.waitKey(0)
cv2.destroyAllWindows()