import numpy as np
from collections import defaultdict
from cm_sketch import *
from decoder import *  # 你已有的解码函数
from cm_analysis import *  # 你已有的分析函数


# # 加载流 ID
# def load_flow_ids(path, limit=120000):
#     with open(path, 'r') as f:
#         flow_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
#     return flow_ids

# # 构建 ground truth
# def build_true_counts(flow_list):
#     true_counts = defaultdict(int)
#     for fid in flow_list:
#         true_counts[fid] += 1
#     return true_counts

# # 主测试流程
# def test_cm_decode():
#     flow_list = load_flow_ids("synthetic_00000.txt")
#     true_counts = build_true_counts(flow_list)
#     print("Total packets in dataset:", len(flow_list))
#     print("Unique flows in dataset:", len(true_counts))
    
#     keys = list(true_counts.keys())

#     # 初始化第一层 CM Sketch（3 行，100000 列，2-bit）
#     cm = cm_sketch(cm_d=3, cm_w=60000)
#     for fid in flow_list:
#         cm.insert_dict({fid: 1})

#     # 解码
#     decoded, undecoded = decode_cm_sketch(keys, cm)

#     # 统计信息
#     decoded_total = len(decoded)
#     total_flows = len(keys)
#     success_ratio = decoded_total / total_flows

#     query_errors = []
#     for fid in undecoded:
#         est = cm.query_one(fid)
#         real = true_counts[fid]
#         rel_err = abs(est - real) / real
#         query_errors.append(rel_err)

#     mean_query_rel_error = np.mean(query_errors) if query_errors else 0.0

#     # 输出结果
#     print(f"Total flows            : {total_flows}")
#     print(f"Decoded flows          : {decoded_total}")
#     print(f"Decode success ratio   : {success_ratio:.4f}")
#     print(f"Mean rel. error (rest) : {mean_query_rel_error:.4f}")

#     # 分析
#     analyze_zero_and_relative_error(keys, decoded)
#     distribution = analyze_flow_size_distribution(true_counts)
#     print("\nFlow size distribution:")

# if __name__ == "__main__":
#    test_cm_decode()


def load_flow_ids(path, limit=340000):
    with open(path, 'r') as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()][:limit]

def build_ground_truth(flow_list):
    counter = defaultdict(int)
    for fid in flow_list:
        counter[fid] += 1
    return counter


def compute_relative_errors_by_size(true_counts, decoded, cm1_dec):
    decoded_buckets = {'1': [], '2': [], '3': [], '4+': []}
    undecoded_buckets = {'1': [], '2': [], '3': [], '4+': []}
    decoded_errors = []

    for fid, real in true_counts.items():
        bucket = '1' if real == 1 else '2' if real == 2 else '3' if real == 3 else '4+'
        if fid in decoded:
            est = decoded[fid]
            err = abs(est - real) / real
            decoded_errors.append(err)
            decoded_buckets[bucket].append(err)
        else:
            est = min(cm1_dec.query_d([fid]).flatten())
            err = abs(est - real) / real
            undecoded_buckets[bucket].append(err)

    return decoded_errors, decoded_buckets, undecoded_buckets

def print_relative_error_summary(decoded_errors, decoded_buckets, undecoded_buckets):
    mean_decoded_rel_error = np.mean(decoded_errors) if decoded_errors else 0.0
    print("====== Decode Result Summary ======")
    print(f"Mean relative error (decoded): {mean_decoded_rel_error:.4f}")

    print("\nMean relative error by flow size (decoded only):")
    for k in ['1', '2', '3', '4+']:
        errs = decoded_buckets[k]
        avg = np.mean(errs) if errs else 0.0
        print(f"  Flow size {k:>2}: {avg:.4f} (based on {len(errs)} flows)")

    print("\nMean relative error by flow size (undecoded only):")
    for k in ['1', '2', '3', '4+']:
        errs = undecoded_buckets[k]
        avg = np.mean(errs) if errs else 0.0
        print(f"  Flow size {k:>2}: {avg:.4f} (based on {len(errs)} flows)")

def run_test(file_path):
    threshold1 = 3  # 2-bit overflow threshold
    flow_list = load_flow_ids(file_path)
    true_counts = build_ground_truth(flow_list)
    flow_keys = list(true_counts.keys())

    # Build two-level sketch with control plane
    cm1 = cm_sketch(cm_d=2, cm_w=120000)
    cm2 = cm_sketch(cm_d=2, cm_w=15000)
    data_plane = cm_sketch_nlevel([cm1, cm2], [2, 8])
    controlled = cm_sketch_controlled(data_plane)

    for fid in flow_list:
        controlled.insert(fid)

    # Decode using only data_plane sketches
    cm1_dec = controlled.data_plane.cm_list[0]
    cm2_dec = controlled.data_plane.cm_list[1]
    decoded, undecoded = decode_two_level_sketch(flow_keys, cm1_dec, cm2_dec, threshold1)

    # Summary
    decoded_total = len(decoded)
    undecoded_total = len(undecoded)
    total_flows = len(flow_keys)
    success_ratio = decoded_total / total_flows

    print("====== Decode Success Overview ======")
    print(f"Total flows               : {total_flows}")
    print(f"Successfully decoded flows: {decoded_total}")
    print(f"Undecoded flows           : {undecoded_total}")
    print(f"Decode success ratio      : {success_ratio:.4f}")

    # Relative error stats
    decoded_errors, decoded_buckets, undecoded_buckets = compute_relative_errors_by_size(
        true_counts, decoded, cm1_dec
    )
    print_relative_error_summary(decoded_errors, decoded_buckets, undecoded_buckets)

    # Per-size success ratio
    analyze_decode_success_by_flow_size(true_counts, decoded)


    print("\n====== Direct Query from cm_sketch_controlled ======")
    total_error = []
    direct_query_buckets = {'1': [], '2': [], '3': [], '4+': []}

    for fid in flow_keys:
        est = controlled.query(fid)
        real = true_counts[fid]
        err = abs(est - real) / real
        total_error.append(err)

        bucket = '1' if real == 1 else '2' if real == 2 else '3' if real == 3 else '4+'
        direct_query_buckets[bucket].append(err)

    mean_total = np.mean(total_error)
    print(f"Mean relative error (direct query): {mean_total:.4f}")
    print("\nRelative error by flow size (direct query):")
    for k in ['1', '2', '3', '4+']:
        avg = np.mean(direct_query_buckets[k]) if direct_query_buckets[k] else 0.0
        print(f"  Flow size {k:>2}: {avg:.4f} (based on {len(direct_query_buckets[k])} flows)")



if __name__ == "__main__":
    run_test("00000.txt")
