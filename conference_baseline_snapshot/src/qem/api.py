import torch
import numpy as np
import os
from qem.mitigator import QuantumErrorMitigator

class QEM_API:
    """
    The main Interface for the Quantum Error Mitigation (QEM) pipeline
    This class handles:
    1. Loading the pre-trained noise-aware model
    2. Preprocessing input data (concatenating circuit metadata)
    3. Performing inference to recover ideal probability distributions
    """
    def __init__(self, weights_path="weights/best_model_weights_updated.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = QuantumErrorMitigator()
        
        # Reproducibility Check
        if not os.path.exists(weights_path):
             raise FileNotFoundError(f"Weight file '{weights_path}' not found! Please ensure it is in the submission folder.")

        try:
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
            # print("Model loaded successfully")
        except Exception as e:
            raise Exception(f"Error loading model weights: {e}")
        
        self.model.to(self.device)
        self.model.eval()

    def mitigate(self, noisy_probs, metadata):
        """
        Apply the mitigation model to noisy quantum measurements.
        
        Args:
            noisy_probs (np.array): The 16 noisy probabilities (Unmitigated)
            metadata (np.array): [n_qubits, n_gates, depth, noise_level]
                                 This enables 'Noise-Aware' mitigation
            
        Returns:
            clean_probs (np.array): The estimated ideal probability distribution
        """
        # We concatenate the circuit metadata (depth, noise strength) with the 
        # noisy probabilities so the model can adapt to different noise conditions
        full_input = np.concatenate([metadata, noisy_probs])
        
        input_tensor = torch.tensor(full_input, dtype=torch.float32).unsqueeze(0) # Add batch dimension
        input_tensor = input_tensor.to(self.device)
        
        # Inference
        with torch.no_grad():
            log_output = self.model(input_tensor)

            # We convert LogSoftmax back to standard probabilities to ensure
            # the result is a valid distribution (sums to 1)
            clean_probs = torch.exp(log_output).cpu().numpy()[0]
            
        return clean_probs