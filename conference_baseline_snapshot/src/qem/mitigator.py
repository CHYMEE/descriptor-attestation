import torch
import torch.nn as nn

class QuantumErrorMitigator(nn.Module):
    def __init__(self):
        super(QuantumErrorMitigator, self).__init__()

        # Input: 16 Noisy Probabilities + 4 Metadata Features (Noise Awareness)
        # We use a Deep Neural Network to capture non-linear noise patterns
        self.net = nn.Sequential(
            nn.Linear(20, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(512, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),

            nn.Linear(512, 16),
            # Physically Motivated Regularizer: 
            # LogSoftmax ensures outputs represent a valid probability distribution
            nn.LogSoftmax(dim=1)
        )

    def forward(self, x):
        return self.net(x)