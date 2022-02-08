from functools import reduce

from enums import *
from scans import *
from dataclasses import is_dataclass
import csv
import pickle
from tqdm import tqdm


def load():
    with open('kMRI_data.pickle', 'rb') as f:
        data = pickle.load(f)
    return data["patients"], data["scans"]


def flatten(data):
    if is_dataclass(data):
        d = data.__dict__
    elif isinstance(data, dict):
        d = data
    else:
        return data
    e = dict()
    for key, value in d.items():
        if isinstance(key, Enum):
            key = key.name
        f = flatten(value)
        if isinstance(f, dict):
            for k, v in f.items():
                e[f'{key}.{k}'] = v
        else:
            e[key] = f
    if isinstance(data, Patient):
        for time_point, scan_id in data.scan_ids.items():
            scan_dict = flattened_scans[scan_id]
            for key, value in scan_dict.items():
                e[f'{time_point.name}.{key}'] = value
    return e


def dicts_to_csv(x, file):
    keys = set.union(*map(lambda y: set(y.keys()), x))
    with open(file, 'w', newline='\n') as f:
        dict_writer = csv.DictWriter(f, keys, restval="")
        dict_writer.writeheader()
        dict_writer.writerows(x)


patients, scans = load()
flattened_scans = dict()
for scan_id, scan in tqdm(scans.items()):
    flattened_scans[scan_id] = flatten(scan)
flattened_patients = dict()
for patient_hash, patient in tqdm(patients.items()):
    flattened_patients[patient_hash] = flatten(patient)

# lists of dictionaries
s = list(flattened_scans.values())
p = list(flattened_patients.values())

dicts_to_csv(s, "scans.csv")
dicts_to_csv(p, "patients.csv")


"""
patient = {
    race: ...,
    gender: ...,
    V0.KL: ...,
    V0.Femur.MultimodalMesh.BoneMesh: ...,
    no nesting! we replaced the nested keys with dot noation
}
pandas
"""

