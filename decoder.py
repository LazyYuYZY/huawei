from collections import defaultdict

def decode_cm_sketch(flow_keys, cm_sketch):
    """
    解码函数：基于可知流键和完整 CM Sketch counter，尝试迭代还原各流量。
    输入：
        - flow_keys: 可知的所有流 ID（列表）
        - cm_sketch: 一个 cm_sketch 实例，支持 query_d()
    输出：
        - decoded_flows: dict{flow_id -> size}
        - undecoded_flows: set(flow_id)
    """

    d = cm_sketch.d
    w = cm_sketch.w
    offset = cm_sketch.offset
    a = cm_sketch.a
    b = cm_sketch.b
    p = cm_sketch.p
    matrix = cm_sketch.Matrix.copy()

    # 建立每个 counter 映射了哪些 flow
    counter_to_flows = defaultdict(set)  # (row, col) -> set(flow_id)
    flow_to_counters = {}  # flow_id -> list of (row, col)

    for fid in flow_keys:
        x = fid + offset
        h = (a * x + b) % p % w
        h_list = h.reshape(-1).tolist()
        counters = [(i, h_list[i]) for i in range(d)]
        flow_to_counters[fid] = counters
        for c in counters:
            counter_to_flows[c].add(fid)

    # 初始化待解码的流和结果
    decoded_flows = {}
    undecoded_flows = set(flow_keys)

    changed = True
    while changed:
        changed = False
        to_decode = set()

        # 找出所有pure counter（仅对应一个流）
        for (row, col), flows in counter_to_flows.items():
            if len(flows) == 1:
                fid = next(iter(flows))
                if fid not in decoded_flows:
                    to_decode.add(fid)

        # 解码pure counter对应的流
        for fid in to_decode:
            if fid not in flow_to_counters:
                continue

            counters = flow_to_counters[fid]
            val = min(matrix[r][c] for (r, c) in counters)
            decoded_flows[fid] = val
            undecoded_flows.discard(fid)
            changed = True

            for (r, c) in counters:
                matrix[r][c] -= val
                counter_to_flows[(r, c)].discard(fid)

            del flow_to_counters[fid]

    return decoded_flows, undecoded_flows


def decode_two_level_sketch(flow_keys, cm1, cm2, threshold1):
    """
    两级解码：先对第一层未溢出的pure counter解码，溢出的进入第二层继续解码。
    返回：
        - decoded_flows: {flow_id: size}
        - undecoded_flows: set
    """
    d = cm1.d
    offset = cm1.offset
    a = cm1.a
    b = cm1.b
    p = cm1.p
    w = cm1.w
    matrix1 = cm1.Matrix.copy()

    # === 第一阶段 ===
    counter_to_flows = defaultdict(set)
    flow_to_counters = {}
    for fid in flow_keys:
        x = fid + offset
        h = (a * x + b) % p % w
        h_list = h.reshape(-1).tolist()
        counters = [(i, h_list[i]) for i in range(d)]
        flow_to_counters[fid] = counters
        for c in counters:
            counter_to_flows[c].add(fid)

    decoded_flows = {}
    level2_candidates = set()
    undecoded_flows = set(flow_keys)

    changed = True
    while changed:
        changed = False
        to_decode = set()
        counter_insert2 = 0
        for (row, col), flows in counter_to_flows.items():
            if matrix1[row][col] >= threshold1:  # 检查是否溢出
                counter_insert2+=1
            if len(flows) == 1:
                fid = next(iter(flows))
                if fid in flow_to_counters:
                    to_decode.add(fid)
        print(f"counter insert2: {counter_insert2}")
        for fid in to_decode:
            counters = flow_to_counters[fid]
            vals = [matrix1[r][c] for (r, c) in counters]
            min_val = min(vals)
            if min_val < threshold1:
                decoded_flows[fid] = min_val
            else:
                level2_candidates.add(fid)
            undecoded_flows.discard(fid)
            changed = True

            for (r, c) in counters:
                matrix1[r][c] -= min_val
                counter_to_flows[(r, c)].discard(fid)

            del flow_to_counters[fid]
    print(f"overflow flows: {len(level2_candidates)}")
    # 将剩下的流也加入第二层候选（即使不是 pure）
    level2_candidates.update(flow_to_counters.keys())

    # === 第二阶段：对第二层所有候选流 pure 解码 ===
    matrix2 = cm2.Matrix.copy()
    offset2 = cm2.offset
    a2 = cm2.a
    b2 = cm2.b
    p2 = cm2.p
    w2 = cm2.w
    d2 = cm2.d
    print(f"First-level decoded: {len(decoded_flows)} flows")
    print(f"Second-level decoding: {len(level2_candidates)} flows")

    counter_to_flows2 = defaultdict(set)
    flow_to_counters2 = {}
    for fid in level2_candidates:
        x = fid + offset2
        h = (a2 * x + b2) % p2 % w2
        h_list = h.reshape(-1).tolist()
        counters = [(i, h_list[i]) for i in range(d2)]
        flow_to_counters2[fid] = counters
        for c in counters:
            counter_to_flows2[c].add(fid)
    # print(counter_to_flows2)
    changed = True
    while changed:
        changed = False
        to_decode2 = set()

        for (row, col), flows in counter_to_flows2.items():
            if len(flows) == 1:
                fid = next(iter(flows))
                if fid in flow_to_counters2:
                    to_decode2.add(fid)

        for fid in to_decode2:
            counters = flow_to_counters2[fid]
            val = min(matrix2[r][c] for (r, c) in counters)
            decoded_flows[fid] = threshold1 + val
            undecoded_flows.discard(fid)
            changed = True

            for (r, c) in counters:
                matrix2[r][c] -= val
                counter_to_flows2[(r, c)].discard(fid)

            del flow_to_counters2[fid]

    return decoded_flows, undecoded_flows