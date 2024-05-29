import torch
import torch.nn as nn


class TinyVGG(nn.Module):
    def __init__(self, hidden_units: int, output_shape: int):
        super(TinyVGG, self).__init__()

        num_channels = hidden_units

        self.block_1 = nn.Sequential(
            nn.Conv2d(3, num_channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1),
            nn.MaxPool2d(kernel_size=2)
        )

        self.block_2 = nn.Sequential(
            nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1),
            nn.MaxPool2d(kernel_size=2)
        )

        self.block_3 = nn.Sequential(
            nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(num_channels, num_channels, kernel_size=3, padding=1),
            nn.MaxPool2d(kernel_size=2)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(num_channels*6*6, hidden_units),
            nn.ReLU(),
            nn.Linear(hidden_units, output_shape)
        )

    def forward(self, x: torch.Tensor):
        x = self.block_1(x)
        x = self.block_2(x)
        x = self.block_3(x)
        x = self.classifier(x)
        return x
