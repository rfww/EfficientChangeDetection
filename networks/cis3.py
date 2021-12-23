import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F
from torch.utils import model_zoo
from torchvision import models
from utils.spp_layer import spatial_pyramid_pool


class CIS_VGGBN(nn.Module):
    def __init__(self, backbone='vgg16', pretrained=True, freeze_backbone=False):
        super(CIS_VGGBN, self).__init__()
        self.output_num = [4,2,1]
        vgg = models.vgg16_bn(pretrained)
        features = list(vgg.features.children())
        self.dec1 = nn.Sequential(*features[:7])  # 160
        self.dec2 = nn.Sequential(*features[7:14])  # 80
        self.dec3 = nn.Sequential(*features[14:24])  # 40
        # self.dec4 = nn.Sequential(*features[17:24])  # 20
        # self.dec5 = nn.Sequential(*features[24:])  # 10

        self.cis1 = nn.Sequential(

            nn.Conv2d(256, 64, 3, padding=1,stride=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )
   
        self.cis2 = nn.Sequential(
            nn.Linear(1344, 128),
            nn.ReLU(),
            nn.Linear(128, 2)
        )
        self.dp = nn.Softmax()
     
    def forward(self, x, y,bt):
        x_f1 = self.dec1(x)
        x_f2 = self.dec2(x_f1)
        x_f3 = self.dec3(x_f2)
        y_f1 = self.dec1(y)
        y_f2 = self.dec2(y_f1)
        y_f3 = self.dec3(y_f2)
        enc  = torch.cat((x_f3, y_f3), 1)
        clc1 = self.cis1(enc)
        spp  = spatial_pyramid_pool(clc1,bt,[clc1.size(2),clc1.size(3)],self.output_num)
        clc2 = self.cis2(spp)
        dp   = self.dp(clc2)
        return x_f1,y_f1,dp
    # def initialize(self):
    #     self.load_state_dict(torch.load('../res/resnet50-19c8e357.pth'), strict=False)
