from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    port: int
    type: str
