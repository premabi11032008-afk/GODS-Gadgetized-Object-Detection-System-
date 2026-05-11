import cv2
import sys

url = 1
print(f"Trying to open {url} ...")
cap = cv2.VideoCapture(url)
if not cap.isOpened():
    print("Failed to open camera.")
    sys.exit(1)

while True:
    success, frame = cap.read()
    if not success or frame is None:
        print("Camera opened, but no frame could be read.")
        break

    cv2.imshow("Camera Feed", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
