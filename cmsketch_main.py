from cm_sketch import *
from cm_analysis import *
from collections import defaultdict

# # 加载数据
# def load_flow_ids(path):
#     with open(path, 'r') as f:
#         return [int(line.strip()) for line in f if line.strip().isdigit()]

# # 初始化
# cm1_bit = 2
# cm2_bit = 24
# cm1 = cm_sketch(cm_d=2, cm_w=230000)  # 2-bit sketch
# cm2 = cm_sketch(cm_d=2, cm_w=10000)   # 32-bit sketch
# combined = cm_sketch_combined(cm1, cm2)
# print("cm1 paramters: d=", cm1.d, "w=", cm1.w, "bit:", cm1_bit)
# print("cm2 paramters: d=", cm2.d, "w=", cm2.w, "bit:", cm2_bit)
# print("all bits: ", cm1.d * cm1.w*cm1_bit + cm2.d * cm2.w*cm2_bit, "bits")

# # 插入数据
# # flow_list = load_flow_ids("./synthetic_00000.txt")
# flow_list = load_flow_ids("./00000.txt")
# for fid in flow_list:
#     combined.insert(fid)

# # Ground truth
# flow_true_counts = defaultdict(int)
# for fid in flow_list:
#     flow_true_counts[fid] += 1

# # 分析
# analyze_zero_and_relative_error(flow_list, combined)
# distribution = analyze_flow_size_distribution(flow_true_counts)
# print("\nFlow size distribution:")
# for k, v in distribution.items():
#     print(f"  {k}: {v:.4f}")

# analyze_error_by_size(flow_true_counts, combined)


# # 载入流ID
# def load_flow_ids(path):
#     with open(path, 'r') as f:
#         return [int(line.strip()) for line in f if line.strip().isdigit()]

# # 初始化三个 CM Sketch
# cm1_bit = 1
# cm2_bit = 2
# cm3_bit = 24
# cm1 = cm_sketch(cm_d=2, cm_w=230000)   # 1-bit (logical)
# cm2 = cm_sketch(cm_d=2, cm_w=20000)    # 2-bit (logical)
# cm3 = cm_sketch(cm_d=2, cm_w=10000)    # 24-bit
# cm_triple = cm_sketch_triple(cm1, cm2, cm3)
# print("cm1 paramters: d=", cm1.d, "w=", cm1.w, "bit:", cm1_bit)
# print("cm2 paramters: d=", cm2.d, "w=", cm2.w, "bit:", cm2_bit)
# print("cm3 paramters: d=", cm3.d, "w=", cm3.w, "bit:", cm3_bit)
# print("all bits: ", cm1.d * cm1.w*cm1_bit + cm2.d * cm2.w*cm2_bit + cm3.d * cm3.w*cm3_bit, "bits")
# # 插入数据
# flow_list = load_flow_ids("00000.txt")
# for fid in flow_list:
#     cm_triple.insert(fid)

# # 计算 ground truth
# flow_true_counts = defaultdict(int)
# for fid in flow_list:
#     flow_true_counts[fid] += 1

# # 进行分析
# analyze_zero_and_relative_error(flow_list, cm_triple)
# distribution = analyze_flow_size_distribution(flow_true_counts)
# print("\nFlow size distribution:")
# for k, v in distribution.items():
#     print(f"  {k}: {v:.4f}")

# analyze_error_by_size(flow_true_counts, cm_triple)


# # 载入流ID
# def load_flow_ids(path):
#     with open(path, 'r') as f:
#         return [int(line.strip()) for line in f if line.strip().isdigit()]

# # 初始化四个 CM Sketch
# cm0_bit = 1
# cm1_bit = 1
# cm2_bit = 2
# cm3_bit = 24
# cm0 = cm_sketch(cm_d=2, cm_w=230000)   # Bloom-like CM0
# cm1 = cm_sketch(cm_d=2, cm_w=230000)   # 1-bit CM1
# cm2 = cm_sketch(cm_d=2, cm_w=20000)    # 2-bit CM2
# cm3 = cm_sketch(cm_d=2, cm_w=10000)    # 24-bit CM3
# cm_quad = cm_sketch_quad(cm0, cm1, cm2, cm3)
# print("cm0 paramters: d=", cm0.d, "w=", cm0.w, "bit:", cm0_bit)
# print("cm1 paramters: d=", cm1.d, "w=", cm1.w, "bit:", cm1_bit)
# print("cm2 paramters: d=", cm2.d, "w=", cm2.w, "bit:", cm2_bit)
# print("cm3 paramters: d=", cm3.d, "w=", cm3.w, "bit:", cm3_bit)
# print("all bits: ", cm0.d * cm0.w*cm0_bit + cm1.d * cm1.w*cm1_bit + cm2.d * cm2.w*cm2_bit + cm3.d * cm3.w*cm3_bit, "bits")

# # 插入数据
# flow_list = load_flow_ids("00000.txt")
# for fid in flow_list:
#     cm_quad.insert(fid)

# # 计算 ground truth
# flow_true_counts = defaultdict(int)
# for fid in flow_list:
#     flow_true_counts[fid] += 1

# # 分析
# analyze_zero_and_relative_error(flow_list, cm_quad)
# distribution = analyze_flow_size_distribution(flow_true_counts)
# print("\nFlow size distribution:")
# for k, v in distribution.items():
#     print(f"  {k}: {v:.4f}")

# analyze_error_by_size(flow_true_counts, cm_quad)

# 加载数据
def load_flow_ids(path):
    with open(path, 'r') as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

# 定义每级的bit宽度与宽度（列数）
# 真实数据集 流量大小分布：0.92，0.03，0.01，0.03
bit_list = [1, 1, 1, 1, 24]
width_list = [128000, 64000, 32000, 16000, 6000]
depth = 2  # 所有 CM 的行数一致
# 合成数据集 流量大小分布：偏度1.6，大于3的流为0.33

# 初始化五个 CM Sketch
cm_list = [cm_sketch(cm_d=depth, cm_w=w) for w in width_list]
nlevel = cm_sketch_nlevel(cm_list, bit_list)

# 打印参数信息
total_bits = 0
for i, (cm, bit) in enumerate(zip(cm_list, bit_list)):
    bits = cm.d * cm.w * bit
    total_bits += bits
    print(f"cm{i} parameters: d={cm.d}, w={cm.w}, bit={bit} => {bits} bits")

print("Total bits used across all levels:", total_bits,"=", total_bits/8, "bytes")

# 插入数据
flow_list = load_flow_ids("00000.txt")[0:340000]
# flow_list = load_flow_ids("synthetic_00000.txt")
for fid in flow_list:
    nlevel.insert(fid)

# 计算 ground truth
flow_true_counts = defaultdict(int)
for fid in flow_list:
    flow_true_counts[fid] += 1

# print("Total unique flows:", len(flow_true_counts))
# 分析
analyze_zero_and_relative_error(flow_list, nlevel)
distribution = analyze_flow_size_distribution(flow_true_counts)
print("\nFlow size distribution:")
for k, v in distribution.items():
    print(f"  {k}: {v:.4f}")

analyze_error_by_size(flow_true_counts, nlevel)
