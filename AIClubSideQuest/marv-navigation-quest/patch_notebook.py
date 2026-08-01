import json

with open('starter_notebook.ipynb', 'r') as f:
    nb = json.load(f)

# Cell 5
nb['cells'][5]['source'] = [
    "# Build Marv's model.\n",
    "# navigation_in_features = 64, navigation_out_features = 32\n",
    "model = MarvNavigationModel(64, 32)\n"
]

# Cell 7
nb['cells'][7]['source'] = [
    "import torch.optim as optim\n",
    "from torch.utils.data import TensorDataset, DataLoader\n",
    "\n",
    "# Load surviving parameters\n",
    "model.load_state_dict(checkpoint, strict=False)\n",
    "\n",
    "# Freeze non-navigation layers\n",
    "for name, param in model.named_parameters():\n",
    "    if not name.startswith('navigation_layer.'):\n",
    "        param.requires_grad = False\n",
    "\n",
    "# Setup training\n",
    "dataset = TensorDataset(X_train, y_train)\n",
    "dataloader = DataLoader(dataset, batch_size=32, shuffle=True)\n",
    "\n",
    "criterion = nn.CrossEntropyLoss()\n",
    "optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=0.001)\n",
    "\n",
    "# Training loop\n",
    "epochs = 200\n",
    "for epoch in range(epochs):\n",
    "    model.train()\n",
    "    for batch_X, batch_y in dataloader:\n",
    "        optimizer.zero_grad()\n",
    "        outputs = model(batch_X)\n",
    "        loss = criterion(outputs, batch_y)\n",
    "        loss.backward()\n",
    "        optimizer.step()\n"
]

# Cell 9
nb['cells'][9]['source'] = [
    "model.eval()\n",
    "with torch.no_grad():\n",
    "    predictions = model(route_inputs).argmax(1)\n",
    "    route_prediction = [movement_mapping[str(i.item())] for i in predictions]\n",
    "print(' | '.join(route_prediction))\n"
]

with open('starter_notebook.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
