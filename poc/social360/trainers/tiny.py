"""TinyAdapterTrainer: a small real PyTorch classifier that mirrors the base-plus-adapter structure.

This is not an LLM. It exists so gates, versioning and isolation act on real trained artefacts.
A frozen shared base is trained on a synthetic corpus only. Each tenant adapter is a separate
low-rank file trained by gradient descent on CPU and loaded per tenant at inference.
"""
import hashlib
from pathlib import Path

import torch
from torch import nn

from ..store import tokenize

VOCAB_SIZE = 2048
HIDDEN = 32
RANK = 4
LABELS = ("positive", "negative", "question")


def _bucket(token: str) -> int:
    return int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % VOCAB_SIZE


def featurize(texts: list[str]) -> torch.Tensor:
    features = torch.zeros(len(texts), VOCAB_SIZE)
    for row, text in enumerate(texts):
        for token in tokenize(text):
            features[row, _bucket(token)] += 1
    return features


class TinyModel(nn.Module):
    """Frozen base plus a low-rank update: logits = head(hidden) + adapter(hidden)."""

    def __init__(self):
        super().__init__()
        self.encoder = nn.Linear(VOCAB_SIZE, HIDDEN)
        self.head = nn.Linear(HIDDEN, len(LABELS))
        self.adapter_down = nn.Parameter(torch.zeros(HIDDEN, RANK))
        self.adapter_up = nn.Parameter(torch.zeros(RANK, len(LABELS)))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        hidden = torch.tanh(self.encoder(features))
        return self.head(hidden) + hidden @ self.adapter_down @ self.adapter_up

    def base_state(self) -> dict:
        return {k: v for k, v in self.state_dict().items() if not k.startswith("adapter_")}


def train_base(examples: list[dict], output: Path, epochs: int = 200, seed: int = 0) -> Path:
    torch.manual_seed(seed)
    model = TinyModel()
    _fit(model, examples, list(model.encoder.parameters()) + list(model.head.parameters()), epochs, 0.02)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.base_state(), output)
    return output


def _fit(model: TinyModel, examples: list[dict], parameters: list, epochs: int, lr: float) -> None:
    features = featurize([e["text"] for e in examples])
    targets = torch.tensor([LABELS.index(e["label"]) for e in examples])
    optimiser = torch.optim.Adam(parameters, lr=lr)
    for _ in range(epochs):
        optimiser.zero_grad()
        nn.functional.cross_entropy(model(features), targets).backward()
        optimiser.step()


def load_model(base_path: Path, adapter_path: Path | None) -> TinyModel:
    model = TinyModel()
    model.load_state_dict(torch.load(base_path, weights_only=True), strict=False)
    if adapter_path:
        model.load_state_dict(torch.load(adapter_path, weights_only=True), strict=False)
    return model.eval()


def predict(model: TinyModel, texts: list[str]) -> list[str]:
    with torch.no_grad():
        return [LABELS[i] for i in model(featurize(texts)).argmax(dim=1).tolist()]


class TinyAdapterTrainer:
    def __init__(self, base_path: Path, epochs: int = 150, seed: int = 0):
        self.base_path, self.epochs, self.seed = base_path, epochs, seed

    def train(self, examples: list[dict], output: Path, previous: Path | None = None) -> Path:
        torch.manual_seed(self.seed)
        model = load_model(self.base_path, previous)
        if previous is None:
            # A zero start has zero gradient on a product of two factors.
            nn.init.normal_(model.adapter_down, std=0.05)
            nn.init.normal_(model.adapter_up, std=0.05)
        for name, parameter in model.named_parameters():
            parameter.requires_grad = name.startswith("adapter_")
        model.train()
        _fit(model, examples, [model.adapter_down, model.adapter_up], self.epochs, 0.03)
        output.parent.mkdir(parents=True, exist_ok=True)
        torch.save({k: v for k, v in model.state_dict().items() if k.startswith("adapter_")}, output)
        return output


class DegradingTrainer(TinyAdapterTrainer):
    """Test fixture: learns from shuffled labels, so the candidate gets worse."""

    def train(self, examples, output, previous=None):
        rotated = [e | {"label": LABELS[(LABELS.index(e["label"]) + 1) % len(LABELS)]} for e in examples]
        return super().train(rotated, output, previous)


class LeakyTrainer(TinyAdapterTrainer):
    """Test fixture: memorises another tenant's canary into the adapter's stored metadata."""

    def __init__(self, base_path: Path, leaked_text: str, **kwargs):
        super().__init__(base_path, **kwargs)
        self.leaked_text = leaked_text

    def train(self, examples, output, previous=None):
        path = super().train(examples, output, previous)
        state = torch.load(path, weights_only=True)
        state["adapter_metadata"] = torch.tensor(list(self.leaked_text.encode()), dtype=torch.uint8)
        torch.save(state, path)
        return path
