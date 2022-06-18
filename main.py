import base64
import copy
import io
import cv2
import numpy as np
from starlette.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile
import uvicorn
from src import util
from src.body import Body
from src.hand import Hand

body_estimation = Body('model/body_pose_model.pth')
hand_estimation = Hand('model/hand_pose_model.pth')
joints_name = ["Nose", "Neck", "RShoulder", "RElbow", "RWrist", "LShoulder", "LElbow",
               "LWrist", "RHip", "RKnee", "RAnkle", "LHip", "LKnee", "LAnkle", "REye", "LEye", "REar", "LEar"]


def infer(image):
    """
    Infer the pose of the image.
    """
    ori_img = cv2.imdecode(image, cv2.IMREAD_COLOR)  # B,G,R order
    candidate, subset = body_estimation(ori_img)
    canvas = copy.deepcopy(ori_img)
    canvas, body_coor_person = util.draw_bodypose(canvas, candidate, subset)
    # detect hand
    hands_list = util.handDetect(candidate, subset, ori_img)
    all_hand_peaks = []
    hands_id = []
    for x, y, w, is_left, id in hands_list:
        peaks = hand_estimation(ori_img[y:y+w, x:x+w, :])
        peaks[:, 0] = np.where(peaks[:, 0] == 0, peaks[:, 0], peaks[:, 0]+x)
        peaks[:, 1] = np.where(peaks[:, 1] == 0, peaks[:, 1], peaks[:, 1]+y)
        all_hand_peaks.append(peaks)
        hands_id.append(['Left', id] if is_left else ['Right', id])

    canvas = util.draw_handpose(canvas, all_hand_peaks)
    all_hand_peaks = [all_hand_peaks[i].tolist()
                      for i in range(len(all_hand_peaks))
                      if len(all_hand_peaks[i]) > 0]
    return canvas, body_coor_person, all_hand_peaks, len(subset), hands_id


app = FastAPI(title="Pose Estimation", version="0.8")


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/inference")
async def inference(image: UploadFile = File(...), show_result_img: bool = False, keypoints: bool = True):
    """
    Return the pose of an image."""
    contents = await image.read()
    nparr = np.fromstring(contents, np.uint8)
    canvas, body_keypoints, hand_keypoints, num_bodies, hands_id = infer(nparr)
    _, encoded_img = cv2.imencode('.JPG', canvas)
    encoded_img_b64 = base64.b64encode(encoded_img)
    if keypoints:
        return {'joints_name': joints_name,
                'output_image': [{'image_size': {'width': canvas.shape[1], 'height': canvas.shape[0]}, 'num_bodies': num_bodies,
                                  'bodies': [{'body_id': i, 'joint_XYposition': body_keypoints[i]} for i in range(num_bodies)],
                                 'hands': [{'hand_id': hands_id[i][1], 'hand_type': hands_id[i][0], 'joint_XYposition': hand_keypoints[i]}
                                           for i in range(len(hand_keypoints))]}], 'image': encoded_img_b64}
    elif show_result_img:
        return StreamingResponse(io.BytesIO(encoded_img), media_type='image/jpeg')
    else:
        return ("Please set one of the following parameters at least: show_result_img, keypoints")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
