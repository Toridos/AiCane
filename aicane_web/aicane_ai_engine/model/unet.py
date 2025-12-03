import torch, torch.nn as nn
class UNet(nn.Module):
    def __init__(self,num_classes=5):
        super().__init__()
        def CBR(i,o): return nn.Sequential(
            nn.Conv2d(i,o,3,padding=1),nn.BatchNorm2d(o),nn.ReLU(),
            nn.Conv2d(o,o,3,padding=1),nn.BatchNorm2d(o),nn.ReLU())
        self.e1=CBR(1,64); self.p=nn.MaxPool2d(2)
        self.e2=CBR(64,128); self.e3=CBR(128,256); self.e4=CBR(256,512)
        self.u3=nn.ConvTranspose2d(512,256,2,2); self.d3=CBR(512,256)
        self.u2=nn.ConvTranspose2d(256,128,2,2); self.d2=CBR(256,128)
        self.u1=nn.ConvTranspose2d(128,64,2,2); self.d1=CBR(128,64)
        self.out=nn.Conv2d(64,num_classes,1)
    def forward(self,x):
        e1=self.e1(x); e2=self.e2(self.p(e1))
        e3=self.e3(self.p(e2)); e4=self.e4(self.p(e3))
        d3=self.d3(torch.cat([self.u3(e4),e3],1))
        d2=self.d2(torch.cat([self.u2(d3),e2],1))
        d1=self.d1(torch.cat([self.u1(d2),e1],1))
        return self.out(d1)
