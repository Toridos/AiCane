import torch
from model.unet import UNet
import os

os.makedirs("model", exist_ok=True)

model = UNet(num_classes=5)
torch.save(model.state_dict(), "model/unet_floorplan.pth")

print("✔ dummy model saved to model/unet_floorplan.pth")
