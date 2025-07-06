import numpy as np
import random

# 定义一个质数列表，用于哈希函数计算
all_primes = [6296197, 2254201, 7672057, 1002343, 9815713, 3436583, 4359587, 5638753, 8155451, 
              1542091, 3821407, 9382951, 5844031, 4996559, 8137219]

# 记录已经使用过的质数，避免重复使用
used_primes = {}

class BloomFilter:
    def __init__(self, k, m):
        """
        初始化布隆过滤器

        :param k: 哈希函数的数量
        :param m: 布隆过滤器的位数组大小
        """
        self.k = k
        self.m = m
        # 初始化位数组，所有位都置为 False
        self.bit_array = np.zeros(m, dtype=bool)
        # 随机生成 k 个 a 值，用于哈希函数计算
        self.a = np.random.randint(10000, 100000, size=(k, 1))
        # 随机生成 k 个 b 值，用于哈希函数计算
        self.b = np.random.randint(10000, 100000, size=(k, 1))
        # 筛选出未使用过的质数
        available_primes = [p for p in all_primes if p not in used_primes]
        # 从可用质数中随机选择 k 个
        self.p = np.array(random.sample(available_primes, k)).reshape(k, 1)
        # 标记这些质数为已使用
        used_primes.update(dict(zip(self.p.flatten(), [True] * k)))
        # 定义一个偏移量，用于处理 flow_id
        self.offset = 10**6 + 1

    def insert(self, flow_id):
        """
        向布隆过滤器中插入一个 flow_id

        :param flow_id: 要插入的流标识符
        """
        # 对 flow_id 加上偏移量
        x = flow_id + self.offset
        # 计算 k 个哈希值
        h = (self.a * x + self.b) % self.p % self.m
        # 将对应的位设置为 True
        for idx in h.flatten():
            self.bit_array[idx] = True

    def contains(self, flow_id):
        """
        检查布隆过滤器中是否可能包含某个 flow_id

        :param flow_id: 要检查的流标识符
        :return: 如果可能包含返回 True，否则返回 False
        """
        # 对 flow_id 加上偏移量
        x = flow_id + self.offset
        # 计算 k 个哈希值
        h = (self.a * x + self.b) % self.p % self.m
        # 检查所有对应的位是否都为 True
        return all(self.bit_array[idx] for idx in h.flatten())


class CountMinSketch:
    def __init__(self, d=2, w=10000):
        """
        初始化 Count-Min Sketch

        :param d: 矩阵的行数，即哈希函数的数量
        :param w: 矩阵的列数
        """
        self.d = d
        self.w = w
        # 初始化 Count-Min Sketch 矩阵，所有元素都置为 0
        self.Matrix = np.zeros((d, w), dtype=int)
        # 定义一个偏移量，用于处理 flow_id
        self.offset = 10**6 + 1
        # 随机生成 d 个 a 值，用于哈希函数计算
        self.a = np.random.randint(10000, 100000, size=(d, 1))
        # 随机生成 d 个 b 值，用于哈希函数计算
        self.b = np.random.randint(10000, 100000, size=(d, 1))
        # 筛选出未使用过的质数
        available_primes = [p for p in all_primes if p not in used_primes]
        # 从可用质数中随机选择 d 个
        self.p = np.array(random.sample(available_primes, d)).reshape(d, 1)
        # 标记这些质数为已使用
        used_primes.update(dict(zip(self.p.flatten(), [True] * d)))
        self.max_count = 0  # 用于记录 Count-Min Sketch 中counter的最大计数

    def insert(self, flow_id, value=1):
        """
        向 Count-Min Sketch 中插入一个 flow_id 及其对应的值

        :param flow_id: 要插入的流标识符
        :param value: 要插入的值，默认为 1
        """
        # 对 flow_id 加上偏移量
        x = flow_id + self.offset
        # 计算 d 个哈希值
        h = (self.a * x + self.b) % self.p % self.w
        indices = h.flatten()
        # 将对应位置的值加上插入的值
        for i in range(self.d):
            self.Matrix[i][indices[i]] += value
        # 更新最大计数
        for i in range(self.d):
            self.max_count = max(self.max_count, self.Matrix[i][indices[i]])
    
    def query(self, flow_id):
        """
        查询 Count-Min Sketch 中某个 flow_id 的估计值

        :param flow_id: 要查询的流标识符
        :return: 估计值
        """
        # 对 flow_id 加上偏移量
        x = flow_id + self.offset
        # 计算 d 个哈希值
        h = (self.a * x + self.b) % self.p % self.w
        indices = h.flatten()
        # 返回所有对应位置值的最小值
        return min(self.Matrix[i][indices[i]] for i in range(self.d))


class ThreeLevelSketch:
    def __init__(self, k1=3, k2=3, d3=3, m1=240000, m2=60000, w3=10000):
        """
        初始化三层 Sketch 结构

        :param k1: 第一个布隆过滤器的哈希函数数量
        :param k2: 第二个布隆过滤器的哈希函数数量
        :param d3: Count-Min Sketch 的哈希函数数量
        :param m1: 第一个布隆过滤器的位数组大小
        :param m2: 第二个布隆过滤器的位数组大小
        :param w3: Count-Min Sketch 的矩阵列数
        """
        # 初始化第一个布隆过滤器
        self.bloom1 = BloomFilter(k=k1, m=m1)
        # 初始化第二个布隆过滤器
        self.bloom2 = BloomFilter(k=k2, m=m2)
        # 初始化 Count-Min Sketch
        self.cms = CountMinSketch(d=d3, w=w3)
        # 记录每一层上报到控制平面的 flow_id
        self.reported_to_control_plane = {1: set(), 2: set(), 3: set()}

    def insert(self, flow_id, value=1):
        """
        向三层 Sketch 结构中插入一个 flow_id 及其对应的值

        :param flow_id: 要插入的流标识符
        :param value: 要插入的值，默认为 1
        """
        if not self.bloom1.contains(flow_id):
            # 如果第一个布隆过滤器不包含该 flow_id，上报到第一层并插入
            self.reported_to_control_plane[1].add(flow_id)
            self.bloom1.insert(flow_id)
        elif not self.bloom2.contains(flow_id):
            # 如果第一个布隆过滤器包含但第二个不包含，上报到第二层并插入
            self.reported_to_control_plane[2].add(flow_id)
            self.bloom2.insert(flow_id)
        else:
            # 如果前两个布隆过滤器都包含，查询 Count-Min Sketch
            estimate = self.cms.query(flow_id)
            if estimate == 0:
                # 如果估计值为 0，上报到第三层
                self.reported_to_control_plane[3].add(flow_id)
            # 向 Count-Min Sketch 中插入该 flow_id 及其值
            self.cms.insert(flow_id, value)
        

    def query(self, flow_id):
        """
        查询三层 Sketch 结构中某个 flow_id 的估计值

        :param flow_id: 要查询的流标识符
        :return: 估计值
        """
        return self.cms.query(flow_id)

    def get_reported_flows(self):
        """
        获取每一层上报到控制平面的 flow_id 集合

        :return: 一个字典，键为层数，值为对应的 flow_id 集合
        """
        return self.reported_to_control_plane

    def get_report_stats(self):
        """
        获取每一层上报到控制平面的 flow_id 数量

        :return: 一个字典，键为层数，值为对应的 flow_id 数量
        """
        return {level: len(flows) for level, flows in self.reported_to_control_plane.items()}

class FourLevelSketch:
    def __init__(self, k1=2, k2=2, k3=2, d4=3, m1=240000, m2=60000, m3=60000, w4=10000):
        """
        初始化四层 Sketch 结构

        :param k1: 第一个布隆过滤器的哈希函数数量
        :param k2: 第二个布隆过滤器的哈希函数数量
        :param k3: 第三个布隆过滤器的哈希函数数量
        :param d4: Count-Min Sketch 的哈希函数数量
        :param m1: 第一个布隆过滤器的位数组大小
        :param m2: 第二个布隆过滤器的位数组大小
        :param m3: 第三个布隆过滤器的位数组大小
        :param w4: Count-Min Sketch 的矩阵列数
        """
        # 初始化第一个布隆过滤器
        self.bloom1 = BloomFilter(k=k1, m=m1)
        # 初始化第二个布隆过滤器
        self.bloom2 = BloomFilter(k=k2, m=m2)
        # 初始化第三个布隆过滤器
        self.bloom3 = BloomFilter(k=k3, m=m3)
        # 初始化 Count-Min Sketch
        self.cms = CountMinSketch(d=d4, w=w4)
        # 记录每一层上报到控制平面的 flow_id
        self.reported_to_control_plane = {1: set(), 2: set(), 3: set(), 4: set()}
        self.max_count = 0  # 用于记录 Count-Min Sketch 中counter的最大计数

    def insert(self, flow_id, value=1):
        """
        向四层 Sketch 结构中插入一个 flow_id 及其对应的值

        :param flow_id: 要插入的流标识符
        :param value: 要插入的值，默认为 1
        """
        if not self.bloom1.contains(flow_id):
            # 如果第一个布隆过滤器不包含该 flow_id，上报到第一层并插入
            self.reported_to_control_plane[1].add(flow_id)
            self.bloom1.insert(flow_id)
        elif not self.bloom2.contains(flow_id):
            # 如果第一个布隆过滤器包含但第二个不包含，上报到第二层并插入
            self.reported_to_control_plane[2].add(flow_id)
            self.bloom2.insert(flow_id)
            # print(f"Inserted flow_id: {flow_id}, value: {value} into Bloom Filter 2")
        elif not self.bloom3.contains(flow_id):
            # 如果前两个布隆过滤器包含但第三个不包含，上报到第三层并插入
            self.reported_to_control_plane[3].add(flow_id)
            self.bloom3.insert(flow_id)
            # print(f"Inserted flow_id: {flow_id}, value: {value} into Bloom Filter 3")
        else:
            # 如果前三个布隆过滤器都包含，查询 Count-Min Sketch
            estimate = self.cms.query(flow_id)
            if estimate == 0:
                # 如果估计值为 0，上报到第四层
                self.reported_to_control_plane[4].add(flow_id)
            # 向 Count-Min Sketch 中插入该 flow_id 及其值
            self.cms.insert(flow_id, value)
            # print(f"Inserted flow_id: {flow_id}, value: {value}")
    
    def query_cm_max_count(self):
        # 更新最大计数
        print(self.cms.Matrix)
        print(f"Max count in Count-Min Sketch: {np.max(self.cms.Matrix)}")

    def query(self, flow_id):
        """
        查询四层 Sketch 结构中某个 flow_id 的估计值

        :param flow_id: 要查询的流标识符
        :return: 估计值
        """
        return self.cms.query(flow_id)

    def get_reported_flows(self):
        """
        获取每一层上报到控制平面的 flow_id 集合

        :return: 一个字典，键为层数，值为对应的 flow_id 集合
        """
        return self.reported_to_control_plane

    def get_report_stats(self):
        """
        获取每一层上报到控制平面的 flow_id 数量

        :return: 一个字典，键为层数，值为对应的 flow_id 数量
        """
        return {level: len(flows) for level, flows in self.reported_to_control_plane.items()}
    
    def clear(self):
        used_primes.clear()

class FixedHashTable:
    def __init__(self, size, bit_width=8):
        self.size = size
        self.bit_width = bit_width
        self.max_value = (1 << bit_width) - 1
        print(f"Max value: {self.max_value}")
        self.table = [None] * size
        # 定义一个偏移量，用于处理 flow_id
        self.offset = 10**6 + 1
        # 随机生成 d 个 a 值，用于哈希函数计算
        self.a = np.random.randint(10000, 100000)
        # 随机生成 d 个 b 值，用于哈希函数计算
        self.b = np.random.randint(10000, 100000)
        # 筛选出未使用过的质数
        available_primes = [p for p in all_primes if p not in used_primes]
        print(f"used primes: {used_primes}")
        print(f"Available primes: {available_primes}")
        # 从可用质数中随机选择 1 个
        self.p = np.array(random.sample(available_primes, 1)).reshape(1, 1)[0][0]
        # 标记这些质数为已使用
        used_primes.update(dict(zip(self.p.flatten(), [True] * 1)))

        self.overflowed = []   # [(flow_id, overflow_times)]
        self.conflicted = []   # [(evicted_flow_id, counter)]

    def insert(self, flow_id, value):

        # 对 flow_id 加上偏移量
        x = flow_id + self.offset
        # 计算 d 个哈希值
        idx = (self.a * x + self.b) % self.p % self.size
        entry = self.table[idx]

        if entry is None:
            # 新插入
            if value > self.max_value:
                overflow_times = value // (self.max_value + 1)
                residual = value % (self.max_value + 1)
                self.overflowed.append((flow_id, overflow_times))
                self.table[idx] = (flow_id, residual)
            else:
                self.table[idx] = (flow_id, value)
            return

        if entry[0] == flow_id:
            # 累加同 key
            new_val = entry[1] + value
            if new_val > self.max_value:
                overflow_times = new_val // (self.max_value + 1)
                residual = new_val % (self.max_value + 1)
                self.overflowed.append((flow_id, overflow_times))
                self.table[idx] = (flow_id, residual)
            else:
                self.table[idx] = (flow_id, new_val)
            return

        else:
            # 冲突：上报旧条目，替换为新值
            self.conflicted.append((entry[0], entry[1]))
            if value > self.max_value:
                overflow_times = value // (self.max_value + 1)
                residual = value % (self.max_value + 1)
                self.overflowed.append((flow_id, overflow_times))
                self.table[idx] = (flow_id, residual)
            else:
                self.table[idx] = (flow_id, value)
            return


    def query(self, flow_id):
        idx = hash(flow_id) % self.size
        entry = self.table[idx]
        if entry and entry[0] == flow_id:
            return entry[1]
        return 0

    def get_overflowed(self):
        return self.overflowed

    def get_conflicted(self):
        return self.conflicted

