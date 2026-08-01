import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from model import MarvNavigationModel

# Load data
train = np.load("training_data.npz")
X_train = torch.tensor(train["X_train"], dtype=torch.float32)
y_train = torch.tensor(train["y_train"], dtype=torch.long)

val = np.load("validation_data.npz")
X_val = torch.tensor(val["X_validation"], dtype=torch.float32)
y_val = torch.tensor(val["y_validation"], dtype=torch.long)

route_inputs = torch.tensor(np.load("route_inputs.npz")["X_route_inputs"], dtype=torch.float32)
movement_mapping = json.load(open("movement_mapping.json"))

checkpoint = torch.load("damaged_model_state_dict.pt", map_location="cpu", weights_only=True)

# Define model dimensions based on checkpoint
navigation_in_features = checkpoint["input_layer.weight"].shape[0]  # 64
navigation_out_features = checkpoint["output_layer.weight"].shape[1] # 32

model = MarvNavigationModel(navigation_in_features, navigation_out_features)

# Load surviving parameters
load_result = model.load_state_dict(checkpoint, strict=False)

# Freeze non-navigation layers
for name, param in model.named_parameters():
    if not name.startswith("navigation_layer."):
        param.requires_grad = False

# Setup training
dataset = TensorDataset(X_train, y_train)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.001)

# Training loop
epochs = 200
for epoch in range(epochs):
    model.train()
    for batch_X, batch_y in dataloader:
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

# Final completion summary
def marv_completion_summary(model):
    original = torch.load("damaged_model_state_dict.pt", map_location="cpu", weights_only=True)
    reference = MarvNavigationModel(original["input_layer.weight"].shape[0],
                                    original["output_layer.weight"].shape[1])
    load_result = reference.load_state_dict(original, strict=False)

    trainable = [n for n, p in model.named_parameters() if p.requires_grad]
    non_nav_frozen = all(not p.requires_grad for n, p in model.named_parameters()
                         if not n.startswith("navigation_layer."))
    state = model.state_dict()
    unchanged = all(torch.equal(state[k], v) for k, v in original.items())

    model.eval()
    with torch.no_grad():
        predictions = model(X_val).argmax(1)
    accuracy = (predictions == y_val).float().mean().item()
    f1s = []
    for c in range(len(movement_mapping)):
        tp = ((predictions == c) & (y_val == c)).sum().item()
        fp = ((predictions == c) & (y_val != c)).sum().item()
        fn = ((predictions != c) & (y_val == c)).sum().item()
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)

    with torch.no_grad():
        route = [movement_mapping[str(i.item())] for i in model(route_inputs).argmax(1)]

    print(f"Inferred navigation_layer shape: {tuple(model.navigation_layer.weight.shape)}")
    print("Checkpoint load mode: strict=False")
    print(f"Missing keys: {', '.join(load_result.missing_keys)}")
    print(f"Unexpected keys: {', '.join(load_result.unexpected_keys) or 'none'}")
    print(f"Trainable parameters: {', '.join(trainable)}")
    print(f"All non-navigation parameters require_grad=False: {non_nav_frozen}")
    print(f"Frozen parameters unchanged after training: {unchanged}")
    print(f"Validation accuracy: {accuracy:.4f}")
    print(f"Validation macro-F1: {sum(f1s) / len(f1s):.4f}")
    print(f"Predicted route: {' | '.join(route)}")
    return route

route = marv_completion_summary(model)
