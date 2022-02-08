from dataclasses import dataclass, field
from enums import Side, TimePoint, TKR, Race, Gender
from typing import Dict, Tuple


@dataclass()
class MultimodalMesh:
    patient_hash: str
    scan_id: str
    BoneMeshFaces: str = ""
    BoneMeshVertices: str = ""
    BoneShape: str = ""
    CartilageThickness: str = ""
    CartilageT2: str = ""


@dataclass()
class SphericalMaps:
    patient_hash: str
    scan_id: str
    FullBoneShape: str = ""
    MultimodalBoneShape: str = ""
    CartilageThickness: str = ""
    CartilageT2: str = ""


@dataclass()
class Scan:
    patient_hash: str
    time_point: TimePoint
    scan_id: str
    months: int = -1
    age: int = -1
    weight: int = -1
    BMI: int = -1
    KL: int = -1
    Femur: Dict = None
    Tibia: Dict = None
    Patella: Dict = None
    KOOS: int = -1
    WOMAC: int = -1
    TKR: int = -1

    def no_images(self):
        return lambda: {
            "MultimodalMesh": MultimodalMesh(self.patient_hash, self.scan_id),
            "SphericalMaps": SphericalMaps(self.patient_hash, self.scan_id)
        }

    def __post_init__(self):
        for part in ["Femur", "Tibia", "Patella"]:
            if getattr(self, part, None) is None:
                setattr(self, part, self.no_images())
        self.side = Side[self.patient_hash.split('_')[-1]]


@dataclass()
class Patient:
    patient_id: str
    side: Side  # 0, 1
    scan_ids: Dict[TimePoint, str] = field(default_factory=dict) # '{V00: scanid for V00, '
    race: Race = Race(0)
    gender: Gender = Gender(0)
    age: int = -1
    height: float = -1
    weight: float = -1
    BMI: float = -1

    def __post_init__(self):
        self.patient_hash = '{}_{}'.format(self.patient_id, self.side.name)

    def __hash__(self):
        return hash(self.patient_hash)

    def __eq__(self, other):
        return hasattr(other, 'patient_hash') and self.patient_hash == other.patient_hash
