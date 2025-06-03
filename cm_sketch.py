import numpy as np
import random

class cm_sketch:
    def __init__(self, cm_d=3, cm_w=100000, flag=0, dict_cm=None, cm_sketch_load=None):
        self.flag = flag
        self.d = cm_d
        self.w = cm_w
        self.d_list = list(range(self.d))
        self.offset = 10**6 + 1

        if flag==0:
            p_list = [6296197, 2254201, 7672057, 1002343, 9815713, 3436583, 4359587, 5638753, 8155451]
            selected_p = random.sample(p_list, self.d)
            self.a = np.random.randint(10000, 100000, size=(self.d, 1))
            self.b = np.random.randint(10000, 100000, size=(self.d, 1))
            self.p = np.array(selected_p).reshape(self.d, 1)
            self.Matrix = np.zeros((self.d, self.w), dtype=int)
        else:
            self.a = np.array(dict_cm['a'])
            self.b = np.array(dict_cm['b'])
            self.p = np.array(dict_cm['p'])
            self.offset = int(dict_cm['offset'])
            self.Matrix = cm_sketch_load if cm_sketch_load is not None else np.zeros((self.d, self.w), dtype=int)

    def insert_dict(self, flow_dict):
        for x, flow_num in flow_dict.items():
            x = x + self.offset
            h = (self.a * x + self.b) % self.p % self.w
            idx = h.reshape(1, self.d).tolist()[0]
            self.Matrix[self.d_list, idx] += flow_num

    def query_d(self, key):
        x = np.array(key) + self.offset
        x = x.reshape(1, -1)
        h = (self.a * x + self.b) % self.p % self.w
        result = np.zeros((self.d, x.shape[1]), dtype=int)
        for d in range(self.d):
            result[d] = self.Matrix[d][h[d]]
        return result

    def query_one(self, key):
        x = key + self.offset
        h = (self.a * x + self.b) % self.p % self.w
        idx = h.reshape(1, self.d).tolist()[0]
        return min(self.Matrix[self.d_list, idx])

    def clear(self):
        self.Matrix.fill(0)

    def save(self, file_name):
        from rw_files import write_dict
        dict_load = {
            'a': self.a.tolist(),
            'b': self.b.tolist(),
            'p': self.p.tolist(),
            'offset': self.offset,
            'd': self.d,
            'w': self.w
        }
        write_dict(file_name, dict_load)


class cm_sketch_combined:
    def __init__(self, cm1: cm_sketch, cm2: cm_sketch):
        assert cm1.d == cm2.d, "Both sketches must have same number of hash functions"
        self.cm1 = cm1  # 2-bit sketch
        self.cm2 = cm2  # 32-bit sketch
        self.d = cm1.d
        self.offset = cm1.offset
        self.max_val_cm1 = 3  # overflow threshold for 2-bit counters

    def insert(self, key, value=1):
        self.cm1.insert_dict({key: value})
        query_vals = self.cm1.query_d([key]).flatten()
        if all(val > self.max_val_cm1 for val in query_vals):
            self.cm2.insert_dict({key: value})

    def query(self, key):
        cm1_vals = self.cm1.query_d([key]).flatten()
        if all(val >= self.max_val_cm1 for val in cm1_vals):
            return self.max_val_cm1 + self.cm2.query_one(key)
        else:
            return min(cm1_vals)

    def query_detail(self, key):
        cm1_vals = self.cm1.query_d([key]).flatten()
        overflow = all(val >= self.max_val_cm1 for val in cm1_vals)
        cm1_val = min(cm1_vals)
        cm2_val = self.cm2.query_one(key) if overflow else 0
        return {
            'cm1': cm1_val,
            'cm2': cm2_val,
            'total': self.max_val_cm1 + cm2_val,
            'overflow': overflow
        }

    def clear(self):
        self.cm1.clear()
        self.cm2.clear()


class cm_sketch_triple:
    def __init__(self, cm1: cm_sketch, cm2: cm_sketch, cm3: cm_sketch):
        assert cm1.d == cm2.d == cm3.d, "All sketches must have same depth (number of hash functions)"
        self.cm1 = cm1  # 1-bit logic
        self.cm2 = cm2  # 2-bit logic
        self.cm3 = cm3  # 24-bit
        self.d = cm1.d
        self.max_val_cm1 = 1
        self.max_val_cm2 = 3

    def insert(self, key, value=1):
        # 插入 CM1
        self.cm1.insert_dict({key: value})
        cm1_vals = self.cm1.query_d([key]).flatten()

        if all(val > self.max_val_cm1 for val in cm1_vals):
            # 进入 CM2
            self.cm2.insert_dict({key: value})
            cm2_vals = self.cm2.query_d([key]).flatten()
            if all(val > self.max_val_cm2 for val in cm2_vals):
                # 再进入 CM3
                self.cm3.insert_dict({key: value})

    def query(self, key):
        cm1_vals = self.cm1.query_d([key]).flatten()
        if all(val >= self.max_val_cm1 for val in cm1_vals):
            cm2_vals = self.cm2.query_d([key]).flatten()
            if all(val >= self.max_val_cm2 for val in cm2_vals):
                return self.max_val_cm1 + self.max_val_cm2 + self.cm3.query_one(key)
            else:
                return self.max_val_cm1 + min(cm2_vals)
        else:
            return min(cm1_vals)


    def query_detail(self, key):
        cm1_vals = self.cm1.query_d([key]).flatten()
        cm1_min = min(cm1_vals)
        cm2_vals = self.cm2.query_d([key]).flatten()
        cm2_min = min(cm2_vals)
        cm3_val = self.cm3.query_one(key)

        promoted_to_cm2 = all(val >= self.max_val_cm1 for val in cm1_vals)
        promoted_to_cm3 = promoted_to_cm2 and all(val >= self.max_val_cm2 for val in cm2_vals)

        return {
            'cm1': cm1_min,
            'cm2': cm2_min,
            'cm3': cm3_val,
            'total': cm1_min + cm2_min + cm3_val,
            'promoted_to_cm2': promoted_to_cm2,
            'promoted_to_cm3': promoted_to_cm3
        }

    def clear(self):
        self.cm1.clear()
        self.cm2.clear()
        self.cm3.clear()

class cm_sketch_quad:
    def __init__(self, cm0, cm1, cm2, cm3):
        assert cm0.d == cm1.d == cm2.d == cm3.d, "All sketches must have same depth"
        self.cm0 = cm0  # Bloom-like (1-bit)
        self.cm1 = cm1  # 1-bit CM
        self.cm2 = cm2  # 2-bit CM
        self.cm3 = cm3  # 24-bit CM
        self.d = cm0.d
        self.max_val_cm0 = 1
        self.max_val_cm1 = 1
        self.max_val_cm2 = 3

    def insert(self, key, value=1):
        # Step 1: Bloom check using CM0
        self.cm0.insert_dict({key: value})
        cm0_vals = self.cm0.query_d([key]).flatten()

        if all(val > self.max_val_cm0 for val in cm0_vals):
            # Step 2: Insert into CM1
            self.cm1.insert_dict({key: value})
            cm1_vals = self.cm1.query_d([key]).flatten()

            if all(val > self.max_val_cm1 for val in cm1_vals):
                # Step 3: Insert into CM2
                self.cm2.insert_dict({key: value})
                cm2_vals = self.cm2.query_d([key]).flatten()

                if all(val > self.max_val_cm2 for val in cm2_vals):
                    # Step 4: Insert into CM3
                    self.cm3.insert_dict({key: value})

    def query(self, key):
            cm0_vals = self.cm0.query_d([key]).flatten()
            if all(val >= self.max_val_cm0 for val in cm0_vals):
                cm1_vals = self.cm1.query_d([key]).flatten()
                if all(val >= self.max_val_cm1 for val in cm1_vals):
                    cm2_vals = self.cm2.query_d([key]).flatten()
                    if all(val >= self.max_val_cm2 for val in cm2_vals):
                        return self.max_val_cm0 + self.max_val_cm1 + self.max_val_cm2 + self.cm3.query_one(key)
                    else:
                        return self.max_val_cm0 + self.max_val_cm1 + min(cm2_vals)
                else:
                    return self.max_val_cm0 + min(cm1_vals)
            else:
                return min(cm0_vals)


    def query_detail(self, key):
        cm0_vals = self.cm0.query_d([key]).flatten()
        cm0_min = min(cm0_vals)
        cm1_vals = self.cm1.query_d([key]).flatten()
        cm1_min = min(cm1_vals)
        cm2_vals = self.cm2.query_d([key]).flatten()
        cm2_min = min(cm2_vals)
        cm3_val = self.cm3.query_one(key)

        promoted_to_cm1 = all(val >= self.max_val_cm0 for val in cm0_vals)
        promoted_to_cm2 = promoted_to_cm1 and all(val >= self.max_val_cm1 for val in cm1_vals)
        promoted_to_cm3 = promoted_to_cm2 and all(val >= self.max_val_cm2 for val in cm2_vals)

        return {
            'cm0': cm0_min,
            'cm1': cm1_min,
            'cm2': cm2_min,
            'cm3': cm3_val,
            'total': cm0_min + cm1_min + cm2_min + cm3_val,
            'promoted_to_cm1': promoted_to_cm1,
            'promoted_to_cm2': promoted_to_cm2,
            'promoted_to_cm3': promoted_to_cm3
        }

    def clear(self):
        self.cm0.clear()
        self.cm1.clear()
        self.cm2.clear()
        self.cm3.clear()


class cm_sketch_nlevel:
    def __init__(self, cm_list, bit_list):
        assert len(cm_list) == len(bit_list), "Number of sketches must match number of bit sizes"
        depth_set = set(cm.d for cm in cm_list)
        assert len(depth_set) == 1, "All sketches must have same depth"
        self.cm_list = cm_list
        self.bit_list = bit_list
        self.thresholds = [2 ** b - 1 for b in bit_list]  # 溢出阈值
        self.d = cm_list[0].d
        self.levels = len(cm_list)

    def insert(self, key, value=1):
        for level in range(self.levels):
            self.cm_list[level].insert_dict({key: value})
            vals = self.cm_list[level].query_d([key]).flatten()
            if not all(val > self.thresholds[level] for val in vals):
                break  # 未全部溢出，不再晋升

    def query(self, key):
        total = 0
        for level in range(self.levels):
            vals = self.cm_list[level].query_d([key]).flatten()
            if all(val >= self.thresholds[level] for val in vals):
                total += self.thresholds[level]
            else:
                total += min(vals)
                break
        return total

    def query_detail(self, key):
        details = {}
        total = 0
        promoted_flags = []

        for level in range(self.levels):
            vals = self.cm_list[level].query_d([key]).flatten()
            min_val = min(vals)
            details[f'cm{level}'] = min_val

            if all(val >= self.thresholds[level] for val in vals):
                total += self.thresholds[level]
                promoted_flags.append(True)
            else:
                total += min_val
                promoted_flags.append(False)
                break

        details['total'] = total
        for i, flag in enumerate(promoted_flags):
            details[f'promoted_to_cm{i+1}'] = flag

        return details

    def clear(self):
        for cm in self.cm_list:
            cm.clear()



from collections import defaultdict

# 全局用于互联数据上报
first_packet_ids = set()
final_overflow_ids = set()
min1_after_insert_ids = set()

class cm_sketch_controlled:
    def __init__(self, data_plane: cm_sketch_nlevel):
        self.data_plane = data_plane
        self.overflow_cache = defaultdict(int)  # 控制面缓存（flow_id -> overflow 增量）

    def insert(self, key, value=1):
        cm_list = self.data_plane.cm_list
        thresholds = self.data_plane.thresholds
        d = self.data_plane.d

        # 第一级查询值，如果所有行为0，表示第一次观测到此流
        level0_vals_before = cm_list[0].query_d([key]).flatten()
        if all(val == 0 for val in level0_vals_before):
            first_packet_ids.add(key)

        for level in range(self.data_plane.levels):
            cm_list[level].insert_dict({key: value})
            vals = cm_list[level].query_d([key]).flatten()

            if level == 0 and min(vals) == 1:
                min1_after_insert_ids.add(key)

            if not all(val >= thresholds[level] for val in vals):
                break

            if level == self.data_plane.levels - 1:
                # 数据面溢出，上报到控制面
                self.overflow_cache[key] += thresholds[level]
                final_overflow_ids.add(key)

                # 清空数据面计数器
                x = key + cm_list[level].offset
                h = (cm_list[level].a * x + cm_list[level].b) % cm_list[level].p % cm_list[level].w
                h_indices = h.reshape(1, d).tolist()[0]
                for i in range(d):
                    cm_list[level].Matrix[i][h_indices[i]] = 0

    def query(self, key):
        data_val = self.data_plane.query(key)
        ctrl_val = self.overflow_cache.get(key, 0)
        return data_val + ctrl_val

    def query_detail(self, key):
        detail = self.data_plane.query_detail(key)
        ctrl_val = self.overflow_cache.get(key, 0)
        detail['control_plane'] = ctrl_val
        detail['final_total'] = detail['total'] + ctrl_val
        return detail

    def clear(self):
        self.data_plane.clear()
        self.overflow_cache.clear()
        first_packet_ids.clear()
        final_overflow_ids.clear()
        min1_after_insert_ids.clear()


# 通过记录第一个port辅助做计数
import numpy as np
import random


class cm_sketch_with_firstport:
    def __init__(self, cm_d=3, cm_w=100000):
        self.d = cm_d
        self.w = cm_w
        self.offset = 10**6 + 1

        # 哈希函数参数
        p_list = [6296197, 2254201, 7672057, 1002343, 9815713, 3436583]
        selected_p = random.sample(p_list, self.d)
        self.a = np.random.randint(10000, 100000, size=(self.d, 1))
        self.b = np.random.randint(10000, 100000, size=(self.d, 1))
        self.p = np.array(selected_p).reshape(self.d, 1)

        # Counter 和 First-Port 矩阵
        self.Matrix = np.zeros((self.d, self.w), dtype=int)
        self.FirstPort = np.zeros((self.d, self.w), dtype=int)

        # 上报的首包记录
        self.first_packet_report = {}  # flow_id -> port_id

    def insert(self, flow_id, port_id):
        x = flow_id + self.offset
        h = (self.a * x + self.b) % self.p % self.w
        indices = h.flatten()

        is_first_packet = any(self.Matrix[i][indices[i]] == 0 for i in range(self.d))

        for i in range(self.d):
            self.Matrix[i][indices[i]] += 1
            if is_first_packet:
                self.FirstPort[i][indices[i]] ^= port_id

        if is_first_packet:
            self.first_packet_report[flow_id] = port_id

    def query(self, flow_id):
        x = flow_id + self.offset
        h = (self.a * x + self.b) % self.p % self.w
        indices = h.flatten()
        return min(self.Matrix[i][indices[i]] for i in range(self.d))

    def get_first_port_xor(self, flow_id):
        x = flow_id + self.offset
        h = (self.a * x + self.b) % self.p % self.w
        indices = h.flatten()
        return [self.FirstPort[i][indices[i]] for i in range(self.d)]

    def get_first_packet_report(self):
        return self.first_packet_report
