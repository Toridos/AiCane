import torch
import cv2
import numpy as np
from unet import UNet

def run_segmentation(pre_img_path, model_path="unet_floorplan.pth"):
    model = UNet(n_classes=5)
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    img = cv2.imread(pre_img_path, 0)
    img_resized = cv2.resize(img, (512, 512))
    tensor = torch.FloatTensor(img_resized/255).unsqueeze(0).unsqueeze(0)

    with torch.no_grad():
        pred = model(tensor)
        mask = pred.argmax(dim=1).squeeze().numpy()

    mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)

    np.save("segmentation.npy", mask)
    return mask
