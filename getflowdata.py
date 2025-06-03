import numpy as np
import random
from collections import Counter

# 参数设定
num_flows = 120000
zipf_param = 2
max_flow_size = 10000
min_fid = 200000  # 所有fid都大于150000
max_fid = 1000000

# 随机生成不重复的fid
flow_ids = random.sample(range(min_fid, max_fid), num_flows)

# 生成流大小（Zipf）并限制最大值
flow_sizes = np.random.zipf(a=zipf_param, size=num_flows)
flow_sizes = np.clip(flow_sizes, 1, max_flow_size)

# 展开为数据包序列
packet_list = []
for fid, size in zip(flow_ids, flow_sizes):
    packet_list.extend([fid] * size)

random.shuffle(packet_list)

# 保存为00000.txt格式
with open("synthetic_00000.txt", "w") as f:
    for pid in packet_list:
        f.write(f"{pid}\n")

# 统计流大小区间比例
counter = Counter(flow_sizes)
total = num_flows

size_1 = counter[1] / total
size_2 = counter[2] / total
size_3 = counter[3] / total
size_4plus = sum(v for k, v in counter.items() if k > 3) / total

# 输出
print("Flow size distribution:")
print(f"  Size = 1   : {size_1:.4f}")
print(f"  Size = 2   : {size_2:.4f}")
print(f"  Size = 3   : {size_3:.4f}")
print(f"  Size >= 4  : {size_4plus:.4f}")
print(f"Total packets generated: {len(packet_list)}")
print(f"Output written to: synthetic_00000.txt")
