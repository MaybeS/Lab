from typing import Tuple, List

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models

from models import Model


class LogCoshLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, y_t, y_prime_t):
        ey_t = y_t - y_prime_t
        return torch.mean(torch.log(torch.cosh(ey_t + 1e-12)))


class swish(nn.Module):
    def __init__(self, inplace=True):
        super(swish, self).__init__()
        self.activation = nn.ReLU6(inplace=inplace)

    def forward(self, x):
        return x * (self.relu(x + 3) / 6)


class CalibNet(Model):
    # LOSS = nn.CrossEntropyLoss
    LOSS = LogCoshLoss

    def __init__(self, param: List[int], batch_size: int, regression: bool):
        super(CalibNet, self).__init__()
        self.batch_size_ = batch_size
        self.param = param
        self.regression = regression

        self.feature = self.backbone()
        self.linear = nn.ModuleList([
            nn.Sequential(
              nn.Linear(2048, 512),
              nn.ReLU(),
              nn.Linear(512, 1 if self.regression else parameter),
            ) for parameter in self.param
        ])

    @classmethod
    def new(cls, num_classes: int, parameters: List[int], batch: int, **kwargs):
        return cls(parameters, batch, kwargs['regression'])

    @staticmethod
    def backbone() \
            -> nn.Module:
        feature = models.resnet101(pretrained=True)
        feature.fc = nn.Identity(2048)

        return feature

    def loss(self, *args, **kwargs):
        self.LOSS = nn.MSELoss if self.regression else LogCoshLoss

        try:
            return self.LOSS(*args, **kwargs)
        except TypeError:
            return self.LOSS()

    def forward(self, x: torch.Tensor) \
            -> Tuple[torch.Tensor]:
        feature = self.feature(x)
        results = map(lambda layer: layer(feature), self.linear)

        if self.regression:
            results = map(F.softmax, results)

        return tuple(results)
