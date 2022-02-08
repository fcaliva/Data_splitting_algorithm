import pandas as pd
from enums import TimePoint, Side, Race, Gender
from scans import Scan, MultimodalMesh, Patient, SphericalMaps
from os.path import join, exists
import pickle
from tqdm import tqdm

main_path = '/data/VirtualAging/'
parts = ["Femur", "Tibia", "Patella"]
mm_path = {part: join(main_path, "MultimodalMesh", part) for part in parts}
spherical_path = {part: join(main_path, "SphericalMaps", part) for part in parts}
attrs = {
    "MultimodalMesh": ["BoneMeshFaces", "BoneMeshVertices", "BoneShape", "CartilageThickness", "CartilageT2"],
    "SphericalMaps": ["FullBoneShape", "MultimodalBoneShape", "CartilageThickness", "CartilageT2"]
}


def save():
    with open('/data/VirtualAging/DataLookup/kMRI_data.pickle', 'wb') as f:
        pickle.dump({"patients": patients,
                     "scans": scans}, f)


def fill_data():
    for index, row in tqdm(df.iterrows(), total=len(df.index)):
        patient_id = str(row["ID"])
        time_point = TimePoint(to_int(row["TP"]))
        side = Side[row["side"].strip().title()]
        scan_id = str(row["filename"]).strip().upper()

        patient = get_patient(patient_id, side)
        scan = make_scan(patient.patient_hash, time_point, scan_id)
        patient.scan_ids[time_point] = scan_id

        scan.months = to_int(row["months"])
        patient.race = Race(to_int(row["race"]))
        patient.gender = Gender(to_int(row["gender"]))
        scan.age = to_int(row["age"])
        scan.height = to_int(row["height"])
        scan.weight = to_int(row["weight"])
        scan.BMI = to_int(row["BMI"])
        if time_point == min(patient.scan_ids.keys()):
            patient.age = scan.age
            patient.height = scan.height
            patient.weight = scan.weight
            patient.BMI = scan.BMI
        scan.KL = to_int(row["KL"])
        scan.KOOS = to_int(row["KOOS"])
        scan.WOMAC = to_int(row["WOMAC"])
        scan.TKR = to_bool(row["TKR"])
        for part in parts:
            images = {
                "MultimodalMesh": MultimodalMesh(patient_id, scan_id),
                "SphericalMaps": SphericalMaps(patient_id, scan_id)
            }
            for group in ["MultimodalMesh", "SphericalMaps"]:
                directory = join(main_path, group, part, patient_id, time_point.name, side.name)
                for attr in attrs[group]:
                    file = join(directory, f'{attr}.h5')
                    if exists(file):
                        setattr(images[group], attr, file)
                    else:
                        pass
            setattr(scan, part, images)


def to_int(x):
    if isinstance(x, int):
        return x
    elif isinstance(x, float):
        try:
            return int(round(x))
        except ValueError:
            return -1
    elif isinstance(x, str):
        string = x.strip()
        try:
            return int(string)
        except ValueError:
            return to_int(float(x))


def to_bool(string):
    if not string:
        return False
    return bool(to_int(string))


def make_scan(patient_hash, time_point, scan_id):
    scan = Scan(patient_hash, time_point, scan_id)
    scans[scan_id] = scan
    return scan


def get_patient(patient_id, side):
    p = patients.get(f'{patient_id}_{side.name}', None)
    if p:
        return p
    new_patient = Patient(patient_id, side)
    patients[f'{patient_id}_{side.name}'] = new_patient
    return new_patient


df = pd.read_csv('/data/VirtualAging/demographics/master_paths_DemsProgPainTKR_impute_v3.csv', dtype=str)
patients = dict()
scans = dict()
fill_data()
save()