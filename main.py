import base64
import copy
import io
import cv2
import numpy as np
from starlette.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import RedirectResponse
from src import util
from src.body import Body
from src.hand import Hand

body_estimation = Body('model/body_pose_model.pth')
hand_estimation = Hand('model/hand_pose_model.pth')


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

    for x, y, w, _ in hands_list:
        peaks = hand_estimation(ori_img[y:y+w, x:x+w, :])
        peaks[:, 0] = np.where(peaks[:, 0] == 0, peaks[:, 0], peaks[:, 0]+x)
        peaks[:, 1] = np.where(peaks[:, 1] == 0, peaks[:, 1], peaks[:, 1]+y)
        all_hand_peaks.append(peaks)

    canvas = util.draw_handpose(canvas, all_hand_peaks)
    all_hand_peaks = [all_hand_peaks[i].tolist()
                      for i in range(len(all_hand_peaks))
                      if len(all_hand_peaks[i]) > 0]
    return canvas, body_coor_person, all_hand_peaks


app = FastAPI(title="Pose Estimation", version="0.8")


@app.post("/inference")
async def inference(image: UploadFile = File(...), img_show: bool = True,
                    keypoints_show: bool = True):
    """
    Return the pose of an image."""
    contents = await image.read()
    nparr = np.fromstring(contents, np.uint8)
    canvas, body_keypoints, hand_keypoints = infer(nparr)
    _, encoded_img = cv2.imencode('.PNG', canvas)
    encoded_img = base64.b64encode(encoded_img)

    if img_show and keypoints_show:
        return {'body_keypoints': body_keypoints, 'hand_keypoints': hand_keypoints,
                'image': encoded_img}

    if img_show:
        return StreamingResponse(io.BytesIO(cv2.imencode('.jpg', canvas)[1].tobytes()),
                                 media_type='image/jpeg')
    elif keypoints_show:
        return ({'body_keypoints': {f'Body{i+1}': body_keypoints[i]
                                    for i in range(len(body_keypoints))}},
                {'hand_keypoints': hand_keypoints})
