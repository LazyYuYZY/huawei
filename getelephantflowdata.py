import random

# ------------------- 参数设置部分 -------------------
# 定义总流量数量
num_total_flows = 2100
# 定义小流所占比例
small_ratio = 0.975
# 定义大流所占比例
large_ratio = 0.025
# 计算小流的数量
num_small_flows = int(num_total_flows * small_ratio)
# 计算大流的数量
num_large_flows = num_total_flows - num_small_flows

# 定义端口范围，从 1 到 288
port_range = list(range(1, 289))
# 定义每个流量最少使用的端口数量
min_ports_per_flow = 64
# 定义每个流量最多使用的端口数量
max_ports_per_flow = 288

# ------------------- 小流参数部分（单位 KB） -------------------
# 定义小流的大小范围，从 10KB 到 100KB
small_size_range = (10, 100)
# 定义小流每个数据包的大小为 1KB
small_packet_size_kb = 1

# ------------------- 大流参数部分（单位 GB -> KB） -------------------
# 定义大流的大小范围，从 10GB 到 100GB，转换为 KB
large_size_range = (10 * 1024 * 1024, 100 * 1024 * 1024)
# 定义大流每个数据包的大小为 1.5KB
large_packet_size_kb = 1.5

# 用于存储每个流量 ID 对应的数据包序列
flow_port_chunks = {}
# 用于存储活跃的流量 ID
active_flow_ids = []

# 流量 ID 计数器，从一个大的随机数开始
fid_counter = random.randint(1000000000, 9999999999)

def generate_packets(flow_id, total_bytes, packet_bytes, ports):
    """
    根据给定的流量 ID、总字节数、单个数据包字节数和端口列表生成数据包序列。

    :param flow_id: 流量的唯一标识符
    :param total_bytes: 该流量的总字节数
    :param packet_bytes: 每个数据包的字节数
    :param ports: 该流量使用的端口列表
    :return: 旋转后的数据包序列，格式为 (flow_id, port, packet_size) 元组列表
    """
    # 计算该流量的总数据包数量
    total_pkts = int(total_bytes / packet_bytes)
    # 初始化每个端口的数据包数量，将总数据包数量平均分配到各个端口
    packet_counts = [total_pkts // len(ports)] * len(ports)
    
    # 处理总数据包数量不能被端口数量整除的情况，将余数依次加到前几个端口的数据包数量上
    for i in range(total_pkts % len(ports)):
        packet_counts[i] += 1

    # 存储每个端口的数据包序列
    packet_seq = []
    # 遍历每个端口及其对应的数据包数量
    for i, port in enumerate(ports):
        size = packet_counts[i]
        # 记录大小为1的子流数量
        if size == 1:
            one_subflows.append((flow_id, port))
        # 记录大小为2的子流数量
        if size == 2:
            two_subflows.append((flow_id, port))

        if size==0: # 当size为0时，不生成数据包,并且后续端口肯定也为0，直接退出循环
            packet_seq.append([])
            break

        if size <= 4: # 当size为0时，不生成数据包
            # 若该端口的数据包数量小于等于 4，则生成对应数量的数据包，每个数据包大小为 1
            packet_seq.append([(flow_id, port, 1)] * size)
        else:
            # 若该端口的数据包数量大于 4，先生成 4 个大小为 1 的数据包
            first_part = [(flow_id, port, 1)] * 4
            # 再生成一个大小为剩余数据包数的数据包
            remainder = [(flow_id, port, size - 4)]
            packet_seq.append(first_part + remainder)
        all_subflows.append((flow_id, port))
    # 存储旋转后的数据包序列
    rotated = []
    # 找出所有端口数据包序列中的最大长度
    max_len = max(len(s) for s in packet_seq)
    # 按顺序从每个端口的数据包序列中取出第 i 个数据包，实现轮转包合并
    for i in range(max_len):
        for s in packet_seq:
            if i < len(s):
                rotated.append(s[i])
    return rotated


# 记录所有子流数量
all_subflows = []
# 记录大小为1的子流数量
one_subflows = []
# 记录大小为2的子流数量
two_subflows = []

# ------------------- 生成小流部分 -------------------
# 循环生成小流
for _ in range(num_small_flows):
    # 随机选择一定数量的端口
    ports = random.sample(port_range, random.randint(min_ports_per_flow, max_ports_per_flow))
    # 随机生成小流的总字节数，将 KB 转换为 B
    bytes_total = random.randint(small_size_range[0], small_size_range[1]) * 1024
    # 调用 generate_packets 函数生成数据包序列
    packets = generate_packets(fid_counter, bytes_total, small_packet_size_kb * 1024, ports)
    # 将生成的数据包序列存储到 flow_port_chunks 字典中
    flow_port_chunks[fid_counter] = packets
    # 将当前流量 ID 添加到活跃流量 ID 列表中
    active_flow_ids.append(fid_counter)
    # 流量 ID 计数器加 1
    fid_counter += 1

print("1-subflows:", len(one_subflows))
print("2-subflows:", len(two_subflows))
print("all subflows:", len(all_subflows))

# ------------------- 生成大流部分 -------------------
# 循环生成大流
for _ in range(num_large_flows):
    # 随机选择一定数量的端口
    ports = random.sample(port_range, random.randint(min_ports_per_flow, max_ports_per_flow))
    # 随机生成大流的总字节数，单位已经是 KB，转换为 B
    bytes_total = random.randint(large_size_range[0], large_size_range[1]) * 1024
    # 调用 generate_packets 函数生成数据包序列
    packets = generate_packets(fid_counter, bytes_total, large_packet_size_kb * 1024, ports)
    # 将生成的数据包序列存储到 flow_port_chunks 字典中
    flow_port_chunks[fid_counter] = packets
    # 将当前流量 ID 添加到活跃流量 ID 列表中
    active_flow_ids.append(fid_counter)
    # 流量 ID 计数器加 1
    fid_counter += 1

print("all subflows:", len(all_subflows))

# ------------------- 全局交叉打乱包部分 -------------------
# 用于存储最终打乱后的数据包序列
final_output = []
# 当还有活跃流量 ID 时，继续循环
while active_flow_ids:
    # 随机选择一个活跃的流量 ID
    fid = random.choice(active_flow_ids)
    # 从对应流量 ID 的数据包序列中取出第一个数据包添加到最终输出列表中
    final_output.append(flow_port_chunks[fid].pop(0))
    # 若该流量 ID 的数据包序列为空，则从活跃流量 ID 列表中移除该 ID
    if not flow_port_chunks[fid]:
        active_flow_ids.remove(fid)

# ------------------- 写入文件部分 -------------------
# 打开文件 flow_port_mixed.txt 以写入模式
with open("flow_port_mixed.txt", "w") as f:
    # 遍历最终输出列表，将每个数据包的信息写入文件
    for fid, pid, size in final_output:
        f.write(f"{fid} {pid} {size}\n")
