import cv2
import mediapipe as mp

## initialize pose estimator
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# get landmark for a specific point
#pose_results.pose_landmarks.landmark[32]

cap = cv2.VideoCapture(0)
while cap.isOpened():
    # read frame
    _, frame = cap.read()
    try:
        # resize the frame for portrait video
        # frame = cv2.resize(frame, (350, 600))
        # convert to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # process the frame for pose detection
        pose_results = pose.process(frame_rgb)
        # print(pose_results.pose_landmarks)
        
        # draw skeleton on the frame
        #print(pose_results.pose_landmarks)

        # print all of the joint positions to the screen
        if pose_results.pose_landmarks is not None:
            
            for idx, res in enumerate(pose_results.pose_landmarks.landmark):
                #print(idx, res)
                h, w, c = frame.shape
                cx, cy = int(res.x*w), int(res.y*h)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
                # draw the list index of the landmark instead of a circle
                #cv2.putText(frame, str(pose_results.pose_landmarks.landmark.index(res)), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                cv2.putText(frame, str(idx), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        # display the frame
        cv2.imshow('Output', frame)
    except Exception as e: 
        print(e)
        break
        
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()