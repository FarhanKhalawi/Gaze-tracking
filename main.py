import cv2
from gaze_tracking import MediaPipeEyeTracker


def main():
    tracker = MediaPipeEyeTracker()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        position, _, right_eye_crop, left_eye_crop = tracker.analyze(frame)

        mesh_coords = tracker.detect_landmarks(frame)
        left_pupil = None
        right_pupil = None
        if mesh_coords:
            left_pupil = mesh_coords[468]
            right_pupil = mesh_coords[473]

        # Set text color
        if position == "LEFT":
            text_color = (255, 0, 0)
        elif position == "RIGHT":
            text_color = (0, 255, 255)
        elif position == "CENTER":
            text_color = (0, 255, 0)
        elif position == "CLOSED":
            text_color = (0, 0, 255)
        else:
            text_color = (255, 255, 255)

        if right_eye_crop is not None:
            cv2.imshow("Right Eye", right_eye_crop)
        if left_eye_crop is not None:
            cv2.imshow("Left Eye", left_eye_crop)

        if position:
            cv2.putText(frame, f"Looking: {position}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, text_color, 2, cv2.LINE_AA)

        # Draw "+" on pupils
        if left_pupil:
            x, y = left_pupil
            cv2.line(frame, (x-5, y), (x+5, y), (0, 255, 0), 2)
            cv2.line(frame, (x, y-5), (x, y+5), (0, 255, 0), 2)

        if right_pupil:
            x, y = right_pupil
            cv2.line(frame, (x-5, y), (x+5, y), (0, 255, 0), 2)
            cv2.line(frame, (x, y-5), (x, y+5), (0, 255, 0), 2)

        cv2.imshow("Eye Gaze Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    tracker.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
