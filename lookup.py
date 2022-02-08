import pickle
from typing import List
import matplotlib.pyplot as plt
from enums import *
from scans import *
import random
from scipy.stats import ks_2samp
import numpy as np
from tqdm import tqdm
from os.path import exists

def load():
    with open('/data/VirtualAging/DataLookup/kMRI_data.pickle', 'rb') as f:
        data = pickle.load(f)
    return data["patients"], data["scans"]


patients, scans = load()
ps = list(patients.values())


def has_tps(patient, tps):
    """
    Has all time points for spherical maps for a patient
    :param patient:
    :param tps: the TimePoints as a list
    :return: if it has all the required time points
    """
    bones = ["Femur", "Tibia", "Patella"]
    for tp in tps:
        if tp not in patient.scan_ids:
            return False
        for bone in bones:
            b = getattr(scans[patient.scan_ids[tp]], bone, dict())
            if "SphericalMaps" not in b:
                return False
            elif b["SphericalMaps"].FullBoneShape == "":
                return False
    return True


def identical(groups):
    """
    Checks for independence between the three groups
    :param groups
    :return: if they are independent
    """

    result = []

    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            a, b = groups[i], groups[j]
            d, p = ks_2samp(a, b)
            result.append((d, p))

    return result

# P[OA | image] = P[OA] P[image | OA]
# 99.9% not OA

# to train our model for aging
matching_1 = list(filter(lambda p: has_tps(p, [TimePoint.V0, TimePoint.V1, TimePoint.V3, TimePoint.V8]), ps))
print(len(matching_1))
for m in matching_1:
    if not hasattr(m, 'tps'):
        m.tps = []
    m.tps.append((TimePoint.V0, TimePoint.V1, TimePoint.V3, TimePoint.V8))

matching_2 = list(filter(lambda p: has_tps(p, [TimePoint.V3, TimePoint.V5, TimePoint.V6, TimePoint.V10]), ps))
print(len(matching_2))
matching_2_prime = []
for m in matching_2:
    if not hasattr(m, 'tps'):
        m.tps = []
    m.tps.append((TimePoint.V3, TimePoint.V5, TimePoint.V6, TimePoint.V10))

matching = matching_1 + matching_2

def splits(group, ratios, s=(7, 6), fully_random=False, graph=False):
    assert sum(ratios) == 1
    patient_map = build_patient_map(group)
    patient_ids = list(patient_map.keys())
    train, val, test = [], [], []
    age_edges = edges(patient_ids, s[0], param_key('age', patient_map))
    bmi_edges = edges(patient_ids, s[1], param_key('BMI', patient_map))
    gender_edges = [1, 2]
    if fully_random:
        age_edges = [0]
        bmi_edges = [0]
        gender_edges = [0]
    print('Age buckets', age_edges)
    print('BMI buckets', bmi_edges)
    for age_group in partition(patient_ids, age_edges, param_key('age', patient_map)):
        for bmi_group in partition(age_group, bmi_edges, param_key('BMI', patient_map)):
            for bucket in partition(bmi_group, gender_edges, param_key('gender', patient_map)):
                if len(bucket) < 10:
                    print('warning: small bucket', len(bucket))
                random.shuffle(bucket)
                pos_0 = round(ratios[0] * len(bucket))
                pos_1 = round((ratios[0] + ratios[1]) * len(bucket))
                for b in bucket[:pos_0]:
                    assert patient_map[b][-1] not in train
                    train.append(patient_map[b].pop())
                for b in bucket[pos_0:pos_1]:
                    assert patient_map[b][-1] not in val
                    val.append(patient_map[b].pop())
                for b in bucket[pos_1:]:
                    assert patient_map[b][-1] not in test
                    test.append(patient_map[b].pop())


    print('sanity check:')
    fig, axs = plt.subplots(3)
    for j, attr in enumerate(['age', 'BMI']):
        g = [..., ..., ...]
        for i, t in enumerate([train, val, test]):
            g[i] = np.array(list(map(lambda p: attr_gettr(p, attr), t)))
            print(f"{attr}, mean = {np.mean(g[i])}, var = {np.var(g[i])}")
        print(identical([g[0], g[1], g[2]]))
        b = 2 if attr == 'gender' else 15
        axs[j].hist(g[0], bins=b, alpha=0.5, label="train")
        axs[j].hist(g[1], bins=b, alpha=0.5, label="val")
        axs[j].hist(g[2], bins=b, alpha=0.5, label ="test")
        print()
    if graph:
        plt.show()
    print()
    if not fully_random:
        print('Comparison fully random:')
        splits(group, ratios, fully_random=True)
    return train, val, test


def param_key(param, patient_map):
    def f(p):
        return attr_gettr(patient_map[p][0], param)
    return f


def attr_gettr(p, name):
    attr = getattr(p, name, None)
    if isinstance(attr, Enum):
        attr = attr.value
    return attr


def partition(items, edges: List, key=lambda x: x):
    buckets = [[] for _ in range(len(edges))]
    for item in items:
        for j in reversed(range(len(edges))):
            if key(item) >= edges[j]:
                buckets[j].append(item)
                break
    assert sum(map(len, buckets)) == len(items)
    return buckets


def edges(items, num_bins, key=lambda x: x):
    n = len(items) // num_bins
    items = sorted(map(key, items))
    edge_array = [items[0]]
    index = 0
    for _ in range(num_bins - 1):
        target = index + n
        fwd = target
        rev = target - 1
        while items[fwd] == items[fwd + 1] and items[rev] == items[rev + 1]:
            fwd += 1
            rev -= 1
        index = 1 + min(fwd, rev, key=lambda x: abs(x - target))
        edge_array.append(items[index])
    return edge_array


def build_patient_map(group: List[Patient]):
    patient_map = dict()
    for p_obj in group:
        pid = p_obj.patient_id
        lst = patient_map.get(pid, [])
        lst.append(p_obj)
        patient_map[pid] = lst
    return patient_map


def relevant(p):
    assert (len(p.tps) == 1) or (len(p.tps) == 2 and p.tps[0] != p.tps[1]), f'{p.patient_hash} {p.tps}'
    return [(p.patient_hash, tps) for tps in p.tps]


train, val, test = splits(matching, [0.7, 0.15, 0.15], [6, 6])
assert all([len(g) == len(set(g)) for g in [train, val, test]])
with open('/data/VirtualAging/DataLookup/aging_splits_2.pickle', 'wb') as f:
    pickle.dump({'train': list(sum(map(relevant, train), [])),
                 'val': list(sum(map(relevant, val), [])),
                 'test': list(sum(map(relevant, test), []))
                 }, f)
print("Splits pickle saved in /data/VirtualAging/DataLookup/aging_splits_2.pickle")


def scan_ids(p):
    s = list(p.scan_ids.values())
    return list(zip(s, map(lambda t: scans[t].KL, s)))


def legit_path(scan_id):
    scan = scans[scan_id]
    bones = ["Femur", "Tibia", "Patella"]
    for bone in bones:
        b = getattr(scan, bone, dict())
        if "SphericalMaps" not in b:
            return False
        elif not exists(b["SphericalMaps"].FullBoneShape):
            return False
    return True


not_matching : List[Patient] = list(set(ps) - set(matching))

for patient in tqdm(not_matching):
    remove_list = []
    for t, s in patient.scan_ids.items():
        if not legit_path(s):
            remove_list.append(t)
    for t in remove_list:
        patient.scan_ids.pop(t, None)

train, val, test = splits(not_matching, [0.7, 0.15, 0.15], [6, 6])
with open('/data/VirtualAging/DataLookup/classification_splits_2.pickle', 'wb') as f:
    pickle.dump({'train': sum(list(map(scan_ids, train)), []),
                 'val': sum(list(map(scan_ids, val)), []),
                 'test': sum(list(map(scan_ids, test)), []),
                 }, f)
print("Splits pickle saved in /data/VirtualAging/DataLookup/classification_splits.pickle")


# 5 ranges
"""
    BMI 40+ 20 samples
    
    0.2 45-50 x [0.5 male, 0.5 female] x [0.2 underweight x 0.2 normal x 0.2 overweight x ...]
    0.2 50-55
    0.2 55-60
    0.2 60-65
    0.2 65+ (yo
"""

# A - E (each have 2 knees)

# train: A1 A2 B1 B2 C1 C2, val: D1 D2, test: E1 E2
# patient_map (dict)
# patient id -> list of patient objects (either len 1 or 2)

# list of patient IDs only
# when do we splits, we split the ratios on Q
# then once we're done splitting

# Q[train] = pids for train split etc.

# we create a new list r which is the spliced version
# for phase in train, test, val:
#        r[phase] = []
#        for q in Q[phase]:
#               r[phase].extend(patient_map[q])



# Age () x Gender x BMI

