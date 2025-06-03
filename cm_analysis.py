import numpy as np
from collections import defaultdict

def analyze_zero_and_relative_error(flow_list, combined, verbose=True):
    """统计零误差比例与平均相对误差"""
    flow_true_counts = defaultdict(int)
    for fid in flow_list:
        flow_true_counts[fid] += 1

    zero_error_count = 0
    relative_errors = []

    for fid, true_val in flow_true_counts.items():
        est_val = combined.query(fid)
        if est_val == true_val:
            zero_error_count += 1
        else:
            rel_error = abs(est_val - true_val) / true_val
            relative_errors.append(rel_error)

    total_flows = len(flow_true_counts)
    zero_error_ratio = zero_error_count / total_flows
    mean_rel_error = np.mean(relative_errors) if relative_errors else 0.0
    all_mean_rel_error = np.sum(relative_errors)/total_flows if relative_errors else 0.0

    if verbose:
        print(f"Total unique flows: {total_flows}")
        print(f"Zero-error flows  : {zero_error_count}")
        print(f"Zero-error ratio  : {zero_error_ratio:.4f}")
        print(f"Mean relative error (non-zero-error): {mean_rel_error:.4f}")
        print(f"Mean relative error (all): {all_mean_rel_error:.4f}")

    return zero_error_ratio, mean_rel_error


def analyze_flow_size_distribution(flow_true_counts):
    """统计流量范围分布比例：=1, =2, =3, 4~7, >=8"""
    bins = {'eq_1': 0, 'eq_2': 0, 'eq_3': 0, '4_7': 0, 'ge_8': 0}

    for count in flow_true_counts.values():
        if count == 1:
            bins['eq_1'] += 1
        elif count == 2:
            bins['eq_2'] += 1
        elif count == 3:
            bins['eq_3'] += 1
        elif 4 <= count <= 7:
            bins['4_7'] += 1
        else:
            bins['ge_8'] += 1

    total = sum(bins.values())
    return {k: v / total for k, v in bins.items()}



def analyze_error_by_size(flow_true_counts, combined):
    """按流量区间输出误差结构：流数、零误差比例、平均相对误差"""
    error_bins = {
        'eq_1': {'total': 0, 'zero': 0, 'rel_errors': []},   # 真实大小 = 1
        'eq_2': {'total': 0, 'zero': 0, 'rel_errors': []},   # 真实大小 = 2
        'eq_3': {'total': 0, 'zero': 0, 'rel_errors': []},   # 真实大小 = 3
        '4_7':  {'total': 0, 'zero': 0, 'rel_errors': []},   # 真实大小 4~7
        'ge_8': {'total': 0, 'zero': 0, 'rel_errors': []},   # 真实大小 ≥8
    }

    def get_bin_name(count):
        if count == 1:
            return 'eq_1'
        elif count == 2:
            return 'eq_2'
        elif count == 3:
            return 'eq_3'
        elif 4 <= count <= 7:
            return '4_7'
        else:
            return 'ge_8'

    for fid, true_val in flow_true_counts.items():
        est_val = combined.query(fid)
        bin_name = get_bin_name(true_val)
        error_bins[bin_name]['total'] += 1

        if est_val == true_val:
            error_bins[bin_name]['zero'] += 1
        else:
            rel_error = abs(est_val - true_val) / true_val
            error_bins[bin_name]['rel_errors'].append(rel_error)

    # 打印结果
    print("\nPer-range error statistics:")
    for bin_name, stats in error_bins.items():
        total = stats['total']
        zero = stats['zero']
        rel_errors = stats['rel_errors']
        zero_ratio = zero / total if total > 0 else 0.0
        mean_rel_error = np.mean(rel_errors) if rel_errors else 0.0

        print(f"  Bin: {bin_name}")
        print(f"    Total flows         : {total}")
        print(f"    Zero-error flows    : {zero}")
        print(f"    Zero-error ratio    : {zero_ratio:.4f}")
        print(f"    Mean relative error : {mean_rel_error:.4f}")


def analyze_decode_success_by_flow_size(flow_true_counts, decoded_flows):
    """统计不同流量大小的解码成功比例"""
    bins = {
        'eq_1': {'total': 0, 'success': 0},
        'eq_2': {'total': 0, 'success': 0},
        'eq_3': {'total': 0, 'success': 0},
        '4_7':  {'total': 0, 'success': 0},
        'ge_8': {'total': 0, 'success': 0},
    }

    def get_bin_name(count):
        if count == 1:
            return 'eq_1'
        elif count == 2:
            return 'eq_2'
        elif count == 3:
            return 'eq_3'
        elif 4 <= count <= 7:
            return '4_7'
        else:
            return 'ge_8'

    for fid, true_val in flow_true_counts.items():
        bin_name = get_bin_name(true_val)
        bins[bin_name]['total'] += 1
        if fid in decoded_flows and decoded_flows[fid] == true_val:
            bins[bin_name]['success'] += 1

    print("\nPer-range decode success ratio:")
    for bin_name, stats in bins.items():
        total = stats['total']
        success = stats['success']
        ratio = success / total if total > 0 else 0.0
        print(f"  Bin: {bin_name}")
        print(f"    Total flows           : {total}")
        print(f"    Successfully decoded  : {success}")
        print(f"    Decode success ratio  : {ratio:.4f}")
