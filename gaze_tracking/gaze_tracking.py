import cv2
import numpy as np
import mediapipe as mp
from gaze_tracking import utils

LEFT_EYE = [362, 385, 387, 263, 373, 380]  
RIGHT_EYE = [33, 160, 158, 133, 153, 144]  


class MediaPipeEyeTracker:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)

    def detect_landmarks(self, frame):
        height, width = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        if result.multi_face_landmarks:
            landmarks = result.multi_face_landmarks[0].landmark
            return [(int(lm.x * width), int(lm.y * height)) for lm in landmarks]
        return None

    def extract_eyes(self, frame, mesh_coords):
        def crop_eye(coords):
            min_x = min(coords, key=lambda p: p[0])[0]
            max_x = max(coords, key=lambda p: p[0])[0]
            min_y = min(coords, key=lambda p: p[1])[1]
            max_y = max(coords, key=lambda p: p[1])[1]
            if min_y >= max_y or min_x >= max_x:
                return None
            return frame[min_y:max_y, min_x:max_x]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = np.zeros_like(gray)

        left_eye = [mesh_coords[i] for i in LEFT_EYE]
        right_eye = [mesh_coords[i] for i in RIGHT_EYE]

        cv2.fillPoly(mask, [np.array(left_eye, dtype=np.int32)], 255)
        cv2.fillPoly(mask, [np.array(right_eye, dtype=np.int32)], 255)

        eyes = cv2.bitwise_and(gray, gray, mask=mask)
        eyes[mask == 0] = 155

        return crop_eye(right_eye), crop_eye(left_eye)

    def estimate_position(self, cropped_eye):
        if cropped_eye is None or cropped_eye.size == 0:
            return "UNKNOWN", [utils.RED, utils.BLACK]

        h, w = cropped_eye.shape[:2]
        if len(cropped_eye.shape) == 3:
            cropped_eye = cv2.cvtColor(cropped_eye, cv2.COLOR_BGR2GRAY)

        blurred = cv2.medianBlur(cv2.GaussianBlur(cropped_eye, (9, 9), 0), 3)
        thresholded = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 33, 0)

        third = w // 3
        sections = [np.sum(thresholded[:, i * third:(i + 1) * third] == 0) for i in range(3)]
        max_idx = np.argmax(sections)

        if np.sum(thresholded == 0) > 0.65 * h * w:  # 👁️ more sensitive blink detection
            return "CLOSED", [utils.RED, utils.BLACK]
        if max_idx == 0 and (sections[0] > sections[1] + 5):
            return "RIGHT", [utils.BLACK, utils.RED]
        elif max_idx == 2 and (sections[2] > sections[1] + 5):
            return "LEFT", [utils.BLACK, utils.RED]
        else:
            return "CENTER", [utils.BLACK, utils.GREEN]

    def analyze(self, frame):
        mesh_coords = self.detect_landmarks(frame)
        if not mesh_coords:
            return "NO FACE", [utils.RED, utils.BLACK], None, None

        right_eye, left_eye = self.extract_eyes(frame, mesh_coords)
        right_pos, _ = self.estimate_position(right_eye)
        left_pos, _ = self.estimate_position(left_eye)

        if right_pos == "CLOSED" and left_pos == "CLOSED":
            position = "CLOSED"
        elif right_pos == "LEFT" or left_pos == "LEFT":
            position = "LEFT"
        elif right_pos == "RIGHT" or left_pos == "RIGHT":
            position = "RIGHT"
        else:
            position = "CENTER"

        return position, [utils.BLACK, utils.GREEN], right_eye, left_eye

    def close(self):
        self.face_mesh.close()
