# Quantum Error Mitigation Using Deep Neural Networks: A Machine Learning Approach

## Document for Journal Publication Preparation

---

# 1. ABSTRACT

This work presents a machine learning-based approach to quantum error mitigation (QEM) using deep neural networks. We developed a noise-aware neural network model that learns to recover ideal quantum circuit output probability distributions from noisy measurements. The model was trained on a synthetic dataset of 30,000 quantum circuit simulations spanning three noise regimes. Our approach achieves a **1.76x improvement** in mean squared error over unmitigated outputs, with a **74.3% win rate** across test samples. The method demonstrates the viability of data-driven error mitigation as a scalable alternative to traditional analytical techniques.

**Keywords:** Quantum Error Mitigation, Machine Learning, Deep Neural Networks, Quantum Computing, Noise Modeling, Qiskit

---

# 2. INTRODUCTION

## 2.1 Problem Statement
Quantum computers are inherently susceptible to noise from various sources including gate errors, decoherence, and measurement imperfections. These errors corrupt the output probability distributions, limiting the practical utility of near-term quantum devices (NISQ era). Traditional error mitigation techniques such as Zero-Noise Extrapolation (ZNE) and Probabilistic Error Cancellation (PEC) require significant overhead and may not scale efficiently.

## 2.2 Proposed Solution
We propose a data-driven approach using deep neural networks to learn the mapping from noisy quantum measurements to ideal probability distributions. The model is "noise-aware," incorporating circuit metadata (qubit count, gate count, depth) and noise level information to adapt its corrections dynamically.

## 2.3 Contributions
1. A synthetic dataset generation pipeline for quantum error mitigation research
2. A noise-aware deep neural network architecture for probability distribution recovery
3. Comprehensive evaluation demonstrating significant improvement over baseline

---

# 3. METHODOLOGY

## 3.1 Dataset Generation

### 3.1.1 Circuit Generation
Random quantum circuits were generated using Qiskit's `random_circuit` function with the following parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Qubits | 2-4 | Number of qubits per circuit |
| Depth | 2-9 | Circuit depth (layers) |
| Max Gates | 50 | Maximum gate count filter |
| Samples | 10,000 circuits × 3 noise levels = 30,000 | Total dataset size |

### 3.1.2 Noise Model Configuration
A composite noise model was implemented using Qiskit-Aer with three error types:

**1. Depolarizing Noise:**
- 1-qubit gates: probability p = λ
- 2-qubit gates: probability p = 2λ
- Applied to gates: `['u1', 'u2', 'u3', 'rx', 'ry', 'rz', 'id', 'sx', 'x', 'cx']`

**2. Amplitude Damping:**
- T₁ relaxation applied to all qubits
- Probability: γ = λ
- For 2-qubit gates: tensor product of individual damping errors

**3. Readout Error:**
- Bit-flip probability during measurement: p = λ
- Symmetric error matrix: `[[1-p, p], [p, 1-p]]`

**Noise Level Configuration:**

| Level | λ Value | Physical Interpretation |
|-------|---------|------------------------|
| Low | 0.05 | High-quality modern hardware |
| Moderate | 0.10 | Older or noisier hardware |
| High | 0.15 | High-noise stress testing regime |

### 3.1.3 Noise Model Implementation (Python/Qiskit)

```python
from qiskit_aer.noise import (NoiseModel, depolarizing_error,
                              amplitude_damping_error, ReadoutError)

def get_noise_model(p_err):
    noise_model = NoiseModel()

    # 1. Depolarizing Error
    error_depol_1q = depolarizing_error(p_err, 1)
    
    # 2. Amplitude Damping (qubit drift towards |0⟩)
    error_damp_1q = amplitude_damping_error(p_err)
    
    # Composition for 1-qubit gates
    full_error_1q = error_depol_1q.compose(error_damp_1q)
    noise_model.add_all_qubit_quantum_error(
        full_error_1q, 
        ['u1', 'u2', 'u3', 'rx', 'ry', 'rz', 'id', 'sx', 'x']
    )

    # 2-qubit gate errors (doubled depolarizing strength)
    error_depol_2q = depolarizing_error(p_err * 2, 2)
    error_damp_2q = error_damp_1q.tensor(error_damp_1q)
    full_error_2q = error_depol_2q.compose(error_damp_2q)
    noise_model.add_all_qubit_quantum_error(full_error_2q, ['cx'])

    # 3. Readout Error
    readout_error = ReadoutError([[1 - p_err, p_err], [p_err, 1 - p_err]])
    noise_model.add_all_qubit_readout_error(readout_error)

    return noise_model
```

### 3.1.4 Data Schema

Each sample in the dataset contains:

| Feature Group | Columns | Dimension | Description |
|---------------|---------|-----------|-------------|
| Metadata | `n_qubits`, `n_gates`, `depth` | 3 | Circuit structural features |
| Noise Context | `noise_level` | 1 | Categorical: 0=Low, 1=Moderate, 2=High |
| Input (X) | `noisy_0` ... `noisy_15` | 16 | Noisy probability vector |
| Target (Y) | `ideal_0` ... `ideal_15` | 16 | Ground truth ideal probabilities |

**Total Features:** 20 input features, 16 output features

---

## 3.2 Model Architecture

### 3.2.1 Network Design
A deep feedforward neural network was designed with the following architecture:

```
Input Layer (20 features)
    ↓
Linear(20 → 512) → BatchNorm1d(512) → ReLU → Dropout(0.2)
    ↓
Linear(512 → 1024) → BatchNorm1d(1024) → ReLU → Dropout(0.2)
    ↓
Linear(1024 → 512) → BatchNorm1d(512) → ReLU
    ↓
Linear(512 → 16) → LogSoftmax
    ↓
Output Layer (16 log-probabilities)
```

### 3.2.2 Design Rationale

1. **Input Features (20):** 16 noisy probabilities + 4 metadata features (n_qubits, n_gates, depth, noise_level) enable noise-aware mitigation

2. **Batch Normalization:** Stabilizes training and accelerates convergence

3. **Dropout (0.2):** Prevents overfitting on the training distribution

4. **LogSoftmax Output:** Ensures outputs represent valid probability distributions (sum to 1) and enables KL divergence loss

### 3.2.3 PyTorch Implementation

```python
import torch
import torch.nn as nn

class QuantumErrorMitigator(nn.Module):
    def __init__(self):
        super(QuantumErrorMitigator, self).__init__()
        
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
            nn.LogSoftmax(dim=1)
        )

    def forward(self, x):
        return self.net(x)
```

---

## 3.3 Training Procedure

### 3.3.1 Training Configuration

| Hyperparameter | Value |
|----------------|-------|
| Optimizer | Adam |
| Learning Rate | 0.0005 |
| Loss Function | KL Divergence (batchmean reduction) |
| Epochs | 500 |
| Train/Test Split | 80% / 20% |
| Random Seed | 42 |

### 3.3.2 Loss Function
Kullback-Leibler Divergence was chosen as the loss function because:
- It measures the difference between two probability distributions
- It is asymmetric, penalizing the model more for assigning low probability to high-probability states
- It naturally pairs with LogSoftmax output

```python
criterion = nn.KLDivLoss(reduction='batchmean')
```

### 3.3.3 Model Selection
Early stopping with best model checkpoint:
- Validation loss monitored every epoch
- Best model weights saved when validation loss improves
- Final model loaded from best checkpoint

---

# 4. RESULTS

## 4.1 Training Performance
- **Best Validation Loss:** 0.5629 (KL Divergence)
- **Convergence:** Model converged within 500 epochs

## 4.2 Test Set Evaluation (6,000 samples)

### 4.2.1 Primary Metrics

| Metric | Unmitigated (Baseline) | AI Model | Improvement |
|--------|------------------------|----------|-------------|
| Mean Squared Error | 0.018641 | 0.010573 | **43.3% reduction** |
| R² Score | 0.1811 | 0.3816 | **+0.20 absolute** |

### 4.2.2 Comparative Analysis

| Metric | Value |
|--------|-------|
| **Improvement Factor** | 1.76× |
| **Win Rate** | 74.30% |

*Win Rate: Percentage of test samples where AI model MSE < Unmitigated MSE*

## 4.3 Interpretation

1. **MSE Reduction:** The model reduces average error by 43.3%, indicating substantial noise suppression

2. **R² Improvement:** The coefficient of determination increases from 0.18 to 0.38, showing the model captures significantly more variance in the ideal distribution

3. **Win Rate:** The model outperforms raw noisy measurements in 74.3% of cases, demonstrating consistent improvement across diverse circuit configurations

4. **Robustness:** The model generalizes across all three noise levels (Low, Moderate, High) without requiring separate models

---

# 5. TECHNICAL IMPLEMENTATION

## 5.1 Inference API

```python
import torch
import numpy as np
from model import QuantumErrorMitigator

class QEM_API:
    """
    Main interface for Quantum Error Mitigation inference.
    """
    def __init__(self, weights_path="best_model_weights.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = QuantumErrorMitigator()
        self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

    def mitigate(self, noisy_probs, metadata):
        """
        Apply mitigation to noisy quantum measurements.
        
        Args:
            noisy_probs (np.array): 16 noisy probabilities
            metadata (np.array): [n_qubits, n_gates, depth, noise_level]
            
        Returns:
            clean_probs (np.array): Estimated ideal probability distribution
        """
        full_input = np.concatenate([metadata, noisy_probs])
        input_tensor = torch.tensor(full_input, dtype=torch.float32).unsqueeze(0)
        input_tensor = input_tensor.to(self.device)
        
        with torch.no_grad():
            log_output = self.model(input_tensor)
            clean_probs = torch.exp(log_output).cpu().numpy()[0]
            
        return clean_probs
```

## 5.2 Usage Example

```python
from mitigate import QEM_API

# Initialize the API
api = QEM_API("best_model_weights.pth")

# Example: Mitigate a noisy measurement
noisy_probs = np.array([0.12, 0.08, 0.15, ...])  # 16 values
metadata = np.array([4, 25, 5, 1])  # [n_qubits, n_gates, depth, noise_level]

clean_probs = api.mitigate(noisy_probs, metadata)
print(f"Mitigated Distribution: {clean_probs}")
```

---

# 6. DEPENDENCIES

## 6.1 Software Requirements

```
torch>=1.9.0
numpy>=1.19.0
pandas>=1.3.0
matplotlib>=3.4.0
seaborn>=0.11.0
scikit-learn>=0.24.0
tqdm>=4.60.0
qiskit>=0.34.0
qiskit-aer>=0.10.0
```

## 6.2 Hardware
- Training performed on Google Colab with GPU acceleration
- Inference compatible with CPU or CUDA-enabled GPU

---

# 7. PROJECT STRUCTURE

```
AQC-QEM-Team11/
├── README.md                       # Project overview
├── requirements.txt                # Python dependencies
├── benchmark.ipynb                 # Model benchmarking notebook
├── best_model_weights_updated.pth  # Pre-trained model weights
├── quantum_dataset_long.csv        # Full dataset (30,000 samples)
│
├── Core-Code/
│   ├── model.py                    # Neural network architecture
│   ├── mitigate.py                 # Inference API
│   ├── best_model_weights.pth      # Model weights
│   └── quantum_dataset_long.csv    # Dataset copy
│
├── Data/
│   ├── README.md                   # Dataset documentation
│   ├── dataset_generation.ipynb    # Qiskit data generation
│   └── quantum_dataset_long.csv    # Dataset copy
│
└── _dump/
    ├── Quantum_Error_Mitigation.ipynb  # Main training notebook
    ├── v2_KLdiv.ipynb                  # KL divergence training
    ├── nn.ipynb                        # Neural network experiments
    └── img/                            # Result visualizations
```

---

# 8. DISCUSSION

## 8.1 Strengths
1. **Scalability:** Once trained, inference is computationally cheap compared to analytical methods
2. **Noise-Awareness:** Single model handles multiple noise regimes via metadata encoding
3. **Generalization:** Trained on random circuits, applicable to diverse circuit structures

## 8.2 Limitations
1. **Circuit Size:** Currently limited to 4 qubits; scaling to larger systems requires architectural changes
2. **Noise Model Specificity:** Trained on specific noise model; real hardware may differ
3. **Distribution Shift:** Performance may degrade on circuits significantly different from training distribution

## 8.3 Future Work
1. **Package Distribution:** Deploy model to PyPI for broader accessibility
2. **Adaptive Techniques:** Use AI to suggest optimal mitigation strategies per circuit
3. **Error Analysis:** Identify circuit parameters that correlate with higher error rates
4. **Hardware Validation:** Test on real quantum hardware (IBM Quantum, etc.)
5. **Larger Systems:** Extend to 8+ qubit circuits with modified architecture

---

# 9. CONCLUSION

We presented a deep learning approach to quantum error mitigation that achieves a 1.76× improvement over unmitigated measurements. The noise-aware neural network architecture successfully learns to recover ideal probability distributions from noisy quantum circuit outputs across multiple noise regimes. This work demonstrates the potential of machine learning as a practical tool for near-term quantum computing applications.

---

# 10. REFERENCES

1. Qiskit Random Circuit Generation: https://quantum.cloud.ibm.com/docs/en/api/qiskit/circuit_random
2. Qiskit-Aer Noise Models: https://qiskit.github.io/qiskit-aer/tutorials/3_building_noise_models.html
3. PyTorch Documentation: https://pytorch.org/docs/stable/index.html
4. Preskill, J. (2018). Quantum Computing in the NISQ era and beyond. Quantum, 2, 79.
5. Temme, K., Bravyi, S., & Gambetta, J. M. (2017). Error mitigation for short-depth quantum circuits. Physical Review Letters, 119(18), 180509.

---

# APPENDIX A: Sample Results

## A.1 Per-Sample Comparison (First 10 Test Samples)

| Sample | Unmitigated MSE | AI Model MSE | Result |
|--------|-----------------|--------------|--------|
| 1 | 0.019328 | 0.011667 | ✓ Better |
| 2 | 0.002215 | 0.004267 | ✗ Worse |
| 3 | 0.012755 | 0.013399 | ✗ Worse |
| 4 | 0.002243 | 0.000260 | ✓ Better |
| 5 | 0.014946 | 0.014004 | ✓ Better |
| 6 | 0.004577 | 0.011582 | ✗ Worse |
| 7 | 0.038150 | 0.000001 | ✓ Better |
| 8 | 0.020751 | 0.018917 | ✓ Better |
| 9 | 0.014594 | 0.003167 | ✓ Better |
| 10 | 0.000626 | 0.000047 | ✓ Better |

---

# APPENDIX B: Hyperparameter Summary

| Category | Parameter | Value |
|----------|-----------|-------|
| **Data** | Total Samples | 30,000 |
| | Train/Test Split | 80/20 |
| | Input Dimension | 20 |
| | Output Dimension | 16 |
| **Architecture** | Hidden Layers | 3 |
| | Hidden Units | 512 → 1024 → 512 |
| | Activation | ReLU |
| | Regularization | Dropout (0.2), BatchNorm |
| | Output Activation | LogSoftmax |
| **Training** | Optimizer | Adam |
| | Learning Rate | 0.0005 |
| | Loss Function | KL Divergence |
| | Epochs | 500 |
| | Best Epoch | ~300 (varies) |

---

*Document prepared for journal publication. All code and data available in the project repository.*
