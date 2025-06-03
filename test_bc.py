# 从 bloom_cm 模块导入所有内容
from bloom_cm import *
# 从 collections 模块导入 defaultdict 和 Counter 类
from collections import defaultdict, Counter
# 导入 math 模块，用于数学计算
import math
# 从 decoder 模块导入所有内容
from decoder import *
from matplotlib import pyplot as plt

# 定义三个不同的 n 值，可能用于后续计算布隆过滤器相关参数
n1 = 120000
n2 = 20000
n3 = 20000
# 定义三个不同的误报率，同样用于布隆过滤器相关计算
fpp1 = 0.3
fpp2 = 0.3
fpp3 = 0.3

# 初始化一个字典，存储各种参数，如布隆过滤器的哈希函数数量、位数组大小等
parameters = {
    'k1': 2, 'k2': 2, 'k3': 2, 'd4': 3, 'm1': 200000, 'm2': 100000, 'm3': 40000, 'w4': 6000 
}
# 以下注释掉的代码用于根据 n 值和误报率动态计算布隆过滤器的位数组大小和哈希函数数量
# parameters["m1"]=int(-1*n1*math.log(fpp1)/(math.log(2)**2))
# parameters['k1']=int(parameters['m1']/n1*math.log(2))
# parameters["m2"]=int(-1*n2*math.log(fpp2)/(math.log(2)**2))
# parameters['k2']=int(parameters['m2']/n2*math.log(2))
# parameters["m3"]=int(-1*n3*math.log(fpp3)/(math.log(2)**2))
# parameters['k3']=int(parameters['m3']/n3*math.log(2))
# 打印当前的参数字典
print(parameters)

def classify_subflows_by_size(path):
    """
    分类子流为三类集合：大小等于1、等于2、大于2。
    返回：eq_1_set, eq_2_set, gt_2_set
    """
    # 使用 defaultdict 初始化一个字典，用于记录每个子流的总大小
    subflow_size = defaultdict(int)

    # 打开指定路径的文件进行读取
    with open(path, "r") as f:
        # 逐行读取文件内容
        for line in f:
            # 将每行内容按空格分割并转换为整数
            fid, port, size = map(int, line.strip().split())
            # 将 flow_id 和 port 拼接成一个唯一的整数作为键
            key = int(f"{fid}{port:03d}")
            # 累加该子流的大小
            subflow_size[key] += size

    # 初始化三个集合，分别用于存储大小等于1、等于2、大于2的子流
    eq_1_set = set()
    eq_2_set = set()
    gt_2_set = set()

    # 遍历记录子流大小的字典
    for key, count in subflow_size.items():
        if count == 1:
            # 若子流大小等于1，添加到 eq_1_set 集合
            eq_1_set.add(key)
        elif count == 2:
            # 若子流大小等于2，添加到 eq_2_set 集合
            eq_2_set.add(key)
        else:
            # 若子流大小大于2，添加到 gt_2_set 集合
            gt_2_set.add(key)

    return eq_1_set, eq_2_set, gt_2_set, subflow_size

def analyze_fp_fn_on_singles(sketch: FourLevelSketch, true_flow_set: set):
    """
    从四层上报中提取只上报过一次的 flow_id，并判断其是否是误报（不在真实集合中）。
    """
    # 所有上报的 flow_id，将 sketch 中各层上报的 flow_id 合并到一个列表中
    all_reported = list(flow for flows in sketch.get_reported_flows().values() for flow in flows)
    # 获取第四层上报的 flow_id 集合
    cm_reported = sketch.get_reported_flows()[4]
    # 筛选出只上报过一次且不在第四层上报集合中的 flow_id
    reported_once = {fid for fid, count in Counter(all_reported).items() if count == 1 and fid not in cm_reported}

    # 过滤出估值为 1 的 flow_id，此处直接使用 reported_once
    reported_once_value1 = reported_once
    # 计算误报的 flow_id 集合，即不在真实集合中但被上报且估值为1的 flow_id
    false_positives = {fid for fid in reported_once_value1 if fid not in true_flow_set}
    # 计算真报的 flow_id 集合，即既在真实集合中又被上报且估值为1的 flow_id
    true_positives = {fid for fid in reported_once_value1 if fid in true_flow_set}

    # 计算上报且估值为1的 flow_id 总数
    total = len(reported_once_value1)
    return {
        'total_queried_once_with_val_1': total,
        'false_positives': len(false_positives),
        'true_positives': len(true_positives),
        'false_positive_rate': len(false_positives) / total if total > 0 else 0.0
    }, reported_once_value1

def analyze_fp_fn_on_gt2(sketch: FourLevelSketch, true_flow_set: set):
    """
    从四层上报中提取只上报过两次的 flow_id，并判断其是否是误报（不在真实集合中）和漏报
    """
    # 所有上报的 flow_id，将 sketch 中各层上报的 flow_id 合并到一个列表中
    all_reported = list(flow for flows in sketch.get_reported_flows().values() for flow in flows)
    # 获取第四层上报的 flow_id 集合
    cm_reported = sketch.get_reported_flows()[4]
    # 筛选出只上报过两次且不在第四层上报集合中的 flow_id
    reported_twice = {fid for fid, count in Counter(all_reported).items() if count == 2 and fid not in cm_reported}

    # 过滤出估值为 2 的 flow_id，此处直接使用 reported_twice
    reported_twice_value2 = reported_twice
    # 计算误报的 flow_id 集合，即不在真实集合中但被上报且估值为2的 flow_id
    false_positives = {fid for fid in reported_twice_value2 if fid not in true_flow_set}
    # 计算真报的 flow_id 集合，即既在真实集合中又被上报且估值为2的 flow_id
    true_positives = {fid for fid in reported_twice_value2 if fid in true_flow_set}

    # 计算上报且估值为2的 flow_id 总数
    total = len(reported_twice_value2)
    return {
        'total_queried_twice_with_val_2': total,
        'false_positives': len(false_positives),
        'true_positives': len(true_positives),
        'false_positive_rate': len(false_positives) / total if total > 0 else 0.0, 
    }, reported_twice_value2

def analyze_fp_fn_on_cm(sketch: FourLevelSketch, true_flow_set: set):
    """
    从四层上报中提取上报过三次或者进入cm的 flow_id，并判断其是否是误报（不在真实集合中）和漏报
    """
    # 所有上报的 flow_id，将 sketch 中各层上报的 flow_id 合并到一个列表中
    all_reported = list(flow for flows in sketch.get_reported_flows().values() for flow in flows)
    # 获取第四层上报的 flow_id 集合
    cm_reported = sketch.get_reported_flows()[4]
    # 筛选出上报过三次或者在第四层上报集合中的 flow_id
    reported_three_or_more = {fid for fid, count in Counter(all_reported).items() if count >= 3 or fid in cm_reported}
    # 计算误报的 flow_id 集合，即不在真实集合中但被上报且进入cm的 flow_id
    false_positives = {fid for fid in reported_three_or_more if fid not in true_flow_set}
    # 计算真报的 flow_id 集合，即既在真实集合中又被上报且进入cm的 flow_id
    true_positives = {fid for fid in reported_three_or_more if fid in true_flow_set}
    # 计算上报且满足条件的 flow_id 总数
    total = len(reported_three_or_more)
    return {
        'total_queried_three_or_more': total,
        'false_positives': len(false_positives),
        'true_positives': len(true_positives),
        'false_positive_rate': len(false_positives) / total if total > 0 else 0.0,
    }, reported_three_or_more

def estimate_fp_fn_rates(sketch: FourLevelSketch, true_flow_set: set) -> dict:
    # 将 sketch 中各层上报的 flow_id 合并到一个集合中
    reported_all = set().union(*sketch.get_reported_flows().values())
    # 计算误报的 flow_id 列表，即不在真实集合中但被上报的 flow_id
    fp = [fid for fid in reported_all if fid not in true_flow_set]
    # 计算漏报的 flow_id 列表，即不在上报集合中但在真实集合中的 flow_id
    fn = [fid for fid in true_flow_set if fid not in reported_all]
    # 计算真实 flow_id 的总数
    total_true = len(true_flow_set)
    # 计算上报 flow_id 的总数
    total_reported = len(reported_all)
    return {
        'true_total': total_true,
        'reported_total': total_reported,
        'false_positives': len(fp),
        'false_negatives': len(fn),
        'false_positive_rate': len(fp) / total_reported if total_reported > 0 else 0.0,
        'false_negative_rate': len(fn) / total_true if total_true > 0 else 0.0
    }

def load_flow_data(file_path):
    """
    加载 flow_port_mixed.txt 文件数据，返回真实流 ID 集合和插入 Sketch 数据
    """
    # 初始化一个集合，用于存储真实的 flow_id
    true_flow_ids = set()
    # 初始化一个 FourLevelSketch 对象，使用 parameters 字典中的参数
    sketch = FourLevelSketch(k1=parameters['k1'], k2=parameters['k2'], k3=parameters['k3'], d4=parameters['d4'], m1=parameters['m1'], m2=parameters['m2'], m3=parameters['m3'], w4=parameters['w4'])
    # 打开指定路径的文件进行读取
    with open(file_path, "r") as f:
        # 逐行读取文件内容
        for line in f:
            # 将每行内容按空格分割并转换为整数
            fid, port, size = map(int, line.strip().split())
            # 将 flow_id 和 port 拼接成一个唯一的整数作为 flow_key
            flow_key = int(f"{fid}{port:03d}")  # flow_id 和 port 拼接成新的唯一 flow ID
            # 将 flow_key 添加到真实 flow_id 集合中
            true_flow_ids.add(flow_key)
            # 将 flow_key 和对应的大小插入到 sketch 中
            sketch.insert(flow_key, size)
    return sketch, true_flow_ids

def query_and_report(sketch, true_flow_ids):
    """
    查询以触发潜在上报，并获取上报统计信息
    """
    # 遍历真实的 flow_id 集合，进行查询操作以触发潜在上报
    for flow_key in true_flow_ids:
        _ = sketch.query(flow_key)

    # 获取数据平面上报的 flow_id 信息
    dataplane_report = sketch.get_reported_flows()

    counter_report = 0

    # 获取各层上报的统计信息
    report_stats = sketch.get_report_stats()
    print("Report Count per Level:")
    # 打印各层上报的 flow_id 数量
    for level, count in report_stats.items():
        a=1# 方便注释
        print(f"  Level {level}: {count} flows reported")
        counter_report += count

    # 打印数据平面上报的 flow_id 数量
    print(f"Dataplane Report: {counter_report} flows reported")
    return dataplane_report, report_stats,counter_report

def refine_eq2_with_fid_majority(eq_1_set, eq_2_set, gt_2_set):
    """
    根据 fid 的多数情况，修正子流分类结果
    """
    # 使用 defaultdict 初始化一个字典，用于存储每个 fid 对应的子流列表
    fid_to_subflows = defaultdict(list)
    # 遍历三个子流集合，将子流按 fid 分组
    for key in eq_1_set | eq_2_set | gt_2_set:
        # 提取子流的 fid 部分
        fid = key // 1000  # int(fid{port:03d}) 提取前部 fid
        fid_to_subflows[fid].append(key)

    # 初始化三个集合，用于存储修正后的子流分类结果
    refined_eq_1 = set()
    refined_eq_2 = set()
    refined_gt_2 = set()
    # 遍历一次上报的子流，修正大流误报为大小为1的小流
    for key in eq_1_set:
        # 提取子流的 fid 部分
        fid = key // 1000
        # 获取该 fid 对应的子流列表
        subflows = fid_to_subflows[fid]
        # 计算该 fid 下大小为1或2的子流数量
        eq2_count = sum(1 for sf in subflows if sf in eq_1_set or sf in eq_2_set)
        # 计算该 fid 下大小大于2的子流数量
        gt2_count = sum(1 for sf in subflows if sf in gt_2_set)

        if gt2_count > eq2_count:
            # 若大小大于2的子流数量不少于大小为1或2的子流数量，将该子流归类到 refined_gt_2 集合
            refined_gt_2.add(key)
        else:
            # 否则，将该子流归类到 refined_eq_1 集合
            refined_eq_1.add(key)
    # 遍历一次上报的子流，修正大流误报为大小为2的小流
    for key in eq_2_set:
        # 提取子流的 fid 部分
        fid = key // 1000
        # 获取该 fid 对应的子流列表
        subflows = fid_to_subflows[fid]
        # 计算该 fid 下大小为1或2的子流数量
        eq2_count = sum(1 for sf in subflows if sf in eq_1_set or sf in eq_2_set)
        # 计算该 fid 下大小大于2的子流数量
        gt2_count = sum(1 for sf in subflows if sf in gt_2_set)

        if gt2_count > eq2_count:
            # 若大小大于2的子流数量不少于大小为1或2的子流数量，将该子流归类到 refined_gt_2 集合
            refined_gt_2.add(key)
        else:
            # 否则，将该子流归类到 refined_eq_2 集合
            refined_eq_2.add(key)
    # 遍历一次上报的子流，修正大流误报为大小大于2的小流
    for key in gt_2_set:
        # 直接将大小大于2的子流添加到 refined_gt_2 集合
        refined_gt_2.add(key)

    return refined_eq_1, refined_eq_2, refined_gt_2

def analyze_fp_fn_by_class(s1_true, s2_true, s3_true, s1_refined, s2_refined, s3_refined):
    """
    分析修正后的子流分类结果与真实分类结果的准确性
    """
    print("=== Refined vs Ground Truth Classification Accuracy ===")
    def report_metrics(refined, true, label):
        """
        报告分类指标，包括真阳性、假阳性、假阴性和准确率
        """
        # 计算真阳性数量，即既在修正集合中又在真实集合中的子流数量
        tp = len(refined & true)
        # 计算假阳性数量，即在修正集合中但不在真实集合中的子流数量
        fp = len(refined - true)
        # 计算假阴性数量，即在真实集合中但不在修正集合中的子流数量
        fn = len(true - refined)
        # 打印分类指标信息
        print(f"{label:<12} | TP: {tp}, FP: {fp}, FN: {fn}, Accuracy: {tp / len(refined) if len(refined) else 0.0:.4f}")

    # 报告大小为1的子流分类指标
    report_metrics(s1_refined, s1_true, "Size = 1")
    # 报告大小为2的子流分类指标
    report_metrics(s2_refined, s2_true, "Size = 2")
    # 报告大小大于2的子流分类指标
    report_metrics(s3_refined, s3_true, "Size > 2")


def analyze_decoded_flows(decoded_flows, s3, sketch, true_flow_size):
    """
    分析解码后的子流，计算平均相对误差和准确解码率。

    :param decoded_flows: 解码后的子流字典，键为子流标识符，值为解码后的子流大小
    :param s3: 存储真实大小大于 2 的子流集合
    :param sketch: 四层 Sketch 对象
    :param true_flow_size: 真实流大小字典，键为子流标识符，值为真实子流大小
    """
    # 计算解码后的子流总数
    total_decoded = len(decoded_flows)
    # 初始化相对误差总和，用于累加所有子流的相对误差
    error_sum = 0
    # 初始化准确解码的子流计数器，用于记录解码大小与真实大小相等的子流数量
    counter_accuracy = 0
    
    # 初始化一个字典，用于存储经过 refined 后的子流和其解码大小
    refined_decoded = {}

    # 遍历解码后的子流字典，fid 为子流的标识符，size 为解码得到的子流大小
    for fid, size in decoded_flows.items():
        # 仅对真实大小大于 2 的子流进行分析，s3 集合存储真实大小大于 2 的子流
        if fid in s3:
            # 遍历 sketch 各层上报的流信息
            for i in range(1, len(sketch.get_reported_flows())):
                # 若该子流出现在某层的上报信息中
                if fid in sketch.get_reported_flows()[i]:
                    # 解码大小加 1
                    size += 1
            refined_decoded[fid] = size
            # 从真实流大小字典中获取该子流的真实大小
            true_size = true_flow_size[fid]
            # 计算解码大小与真实大小之间的相对误差
            error = abs(size - true_size) / true_size
            # 将当前子流的相对误差累加到误差总和中
            error_sum += error
            # 判断解码大小是否与真实大小相等
            if size == true_size:
                # 若相等，准确解码的子流计数器加 1
                counter_accuracy += 1
        else:
            # 若子流不是真实大小大于 2 的子流，直接将其解码大小加入 refined_decoded 字典
            refined_decoded[fid] = size
    return error_sum, total_decoded, counter_accuracy, refined_decoded
    

def main():
    """
    主函数，程序的入口点，负责调用各个功能函数完成子流分类、误报率评估等操作
    """
    # 分类子流，将子流按大小分为三类集合
    s1, s2, s3, true_flow_size = classify_subflows_by_size("flow_port_mixed.txt")
    print(f"Size 1: {len(s1)}")
    print(f"Size 2: {len(s2)}")
    print(f"Size > 2: {len(s3)}")

    # 初始化 Sketch 和 Ground Truth 集合，加载文件数据并插入到 sketch 中
    sketch, true_flow_ids = load_flow_data("flow_port_mixed.txt")

    # 查询并获取上报信息，触发潜在上报并打印各层上报的 flow_id 数量
    dataplane_report, report_stats,counter_report = query_and_report(sketch, true_flow_ids)

    # 评估误报率，计算并打印误报和漏报相关指标
    fp_stats = estimate_fp_fn_rates(sketch, true_flow_ids)
    print("\nFalse Positive Rate Estimation:")
    stats = fp_stats
    print(f"  true total: {stats['true_total']}")
    print(f"  reported total: {stats['reported_total']}")
    print(f"  false positives: {stats['false_positives']}")
    print(f"  false negatives: {stats['false_negatives']}")
    print(f"  false positive rate: {stats['false_positive_rate']:.4f}")
    print(f"  false negative rate: {stats['false_negative_rate']:.4f}")

    # 分析四层上报中只上报过一次的 flow_id，与实际大小为1的 flow_id 对比
    print("\nAnalysis of Reported Flows:")
    analysis, s1_set = analyze_fp_fn_on_singles(sketch, s1)
    print("\nAnalysis of Single-Report Flows:")
    print(f"  Total Queried Once with Value 1: {analysis['total_queried_once_with_val_1']}")
    print(f"  False Positives: {analysis['false_positives']}")
    print(f"  True Positives: {analysis['true_positives']}")
    print(f"  False Positive Rate: {analysis['false_positive_rate']:.4f}")

    # 分析四层上报中只上报过两次的 flow_id，与实际大小为2的 flow_id 对比
    print("\nAnalysis of Double-Report Flows:")
    analysis, s2_set = analyze_fp_fn_on_gt2(sketch, s2)
    print(f"  Total Queried Twice with Value 2: {analysis['total_queried_twice_with_val_2']}")
    print(f"  False Positives: {analysis['false_positives']}")
    print(f"  True Positives: {analysis['true_positives']}")
    print(f"  False Positive Rate: {analysis['false_positive_rate']:.4f}")

    # 分析四层上报中只上报过三次或者进入CM的 flow_id，与实际大小大于2的 flow_id 对比
    print("\nAnalysis of Three-or-More-Report Flows:")
    analysis, s3_set = analyze_fp_fn_on_cm(sketch, s3)
    print(f"  Total Queried Three or More: {analysis['total_queried_three_or_more']}")
    print(f"  False Positives: {analysis['false_positives']}")
    print(f"  True Positives: {analysis['true_positives']}")
    print(f"  False Positive Rate: {analysis['false_positive_rate']:.4f}")

    # 根据 fid 的多数情况修正子流分类结果
    s1_refined ,s2_refined, s3_updated = refine_eq2_with_fid_majority(s1_set, s2_set, s3_set)

    print("\n=== After refine_eq2_with_fid_majority ===")
    print(f"Size 1: {len(s1_refined)}")
    print(f"Refined Size 2: {len(s2_refined)}")
    print(f"Refined Size > 2: {len(s3_updated)}")

    # 分析修正后的子流分类结果与真实分类结果的准确性
    analyze_fp_fn_by_class(s1, s2, s3, s1_refined, s2_refined, s3_updated)

    # 解码 CM Sketch 中的数据，返回解码后的数据包序列和未解码的数据包序列
    decoded_flows, undecoded_flows = decode_cm_sketch(s3_updated, sketch.cms)
    print(f"Decoded flows: {len(decoded_flows)}")
    print(f"Undecoded flows: {len(undecoded_flows)}")
    
    # 对解码后的数据包序列进行分析，计算准确解码率和平均相对误差
    print("\nAnalysis of Decoded Flows:")
    error_sum, total_decoded, counter_accuracy,refined_decoded =analyze_decoded_flows(decoded_flows, s3, sketch, true_flow_size)
    # 若存在解码后的子流
    if total_decoded > 0:
        # 计算平均相对误差，即误差总和除以解码子流总数
        average_error = error_sum / total_decoded
        # 打印解码的子流总数
        print(f"  Total Decoded: {total_decoded}")
        # 打印平均相对误差，保留四位小数
        print(f"  Average Relative Error: {average_error:.4f}")
        # 打印准确数据解码的子流数量
        print(f"  Accurate Decoded: {counter_accuracy}")
        # 打印准确解码率，即准确解码的子流数量除以解码子流总数，保留四位小数
        print(f"  Counter Accuracy: {counter_accuracy / total_decoded:.4f}")
    else:
        a=1#方便注释
        # 若没有解码后的子流，打印提示信息
        print("No decoded flows to analyze.")
    
    print(np.max(sketch.cms.Matrix))

    # 测量无误差的流的数量
    no_error_count = 0
    REs=[]
    for fid in s1_refined:
        if true_flow_size[fid]==1:
            no_error_count += 1
        else:
            RE=abs(true_flow_size[fid]-1)/true_flow_size[fid]
            REs.append(RE)

    print(f"no error count: {no_error_count}")

    for fid in s2_refined:
        if true_flow_size[fid]==2:
            no_error_count += 1
        else:
            RE=abs(true_flow_size[fid]-2)/true_flow_size[fid]
            REs.append(RE)
    
    print(f"no error count: {no_error_count}")
    
    for fid in s3_updated:
        if fid in refined_decoded and refined_decoded[fid]==true_flow_size[fid]:
            no_error_count += 1    
        else:
            if fid in refined_decoded:
                RE=abs(true_flow_size[fid]-refined_decoded[fid])/true_flow_size[fid]
            else:
                RE=abs(true_flow_size[fid]-sketch.query(fid))/true_flow_size[fid]
            REs.append(RE)

    print(f"no error count: {no_error_count}")
    error_count=len(true_flow_ids)-no_error_count
    print(f"error count: {error_count}")

    ARE=np.mean(REs) if len(REs)!=0 else 0

    print(f"average RE: {ARE}")
    # 记录单次实验的结果
    results = {
        "no_error_count": no_error_count,  # 无误差的流的数量
        "error_count": error_count,  # 有误差的流的数量
        "total_inserted": len(true_flow_ids),  # 插入的流的数量
        "total_inserted2cm": s3_updated,  # 进入cms需要解码的流的数量
        "total_cm_decoded": total_decoded,  # 解码的流的数量
        "average_error": np.mean(REs) if len(REs)!=0 else 0,  # 平均相对误差
    }
    sketch.clear()
    return no_error_count,error_count,ARE,counter_report


def plot_cdf(data, title, xlabel, ylabel, filename):
    # 计算CDF
    sorted_data = np.sort(data)
    yvals = np.arange(1, len(sorted_data) + 1) / float(len(sorted_data))

    # 计算分位数
    p5 = np.percentile(data, 5)
    p95 = np.percentile(data, 95)
    # p99 = np.percentile(data, 99)

    # 绘制CDF曲线
    plt.figure(figsize=(8, 5))
    plt.plot(sorted_data, yvals, label='CDF')

    # 添加分位线
    if xlabel=="no_error_count":
        plt.axvline(p5, color='red', linestyle='--', label='5th Percentile')
    else:
        plt.axvline(p95, color='red', linestyle='--', label='95th Percentile')
    # plt.axvline(p99, color='green', linestyle='--', label='99th Percentile')

    # 添加文字标注
    if xlabel=="no_error_count":
        plt.text(p5+100, 0.05, f'5%: {p5:.2f}', color='red', rotation=90, va='bottom')
    else:
        plt.text(p95+100, 0.9, f'95%: {p95:.2f}', color='red', rotation=0, va='bottom')
    # plt.text(p99, 0.05, f'99%: {p99:.2f}', color='green', rotation=90, va='bottom')

    # 添加标题和标签
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # 保存和关闭
    plt.savefig(filename)
    plt.close()




if __name__ == "__main__":
    # 确保脚本作为主程序运行时才调用 main 函数
    test_number=10
    # 运行测试 100 次
    AREs=[]
    no_error_counts=[]
    error_counts=[]
    counter_reports=[]
    print(f"test number: {test_number}")

    # 日志文件
    log_file = "log.txt"

    for i in range(test_number):
        no_error_count,error_count,ARE,counter_report=main()
        AREs.append(ARE)
        no_error_counts.append(no_error_count)
        error_counts.append(error_count)
        counter_reports.append(counter_report)
        # 写入日志文件
        with open(log_file, "a") as f:
            f.write(f"test {i+1}: no_error_count: {no_error_count}, error_count: {error_count}, ARE: {ARE}, counter_report: {counter_report}\n")

    counter_reports=np.array(counter_reports)
    print(f"average counter report: {np.mean(counter_reports)}")


    # 读取日志文件
    with open(log_file, "r") as f:
        no_error_counts = []
        error_counts = []
        AREs = []
        for line in f:
            # 解析日志文件中的数据
            parts = line.strip().split(", ")
            # 提取每个部分的值
            no_error_count = int(parts[0].split(": ")[2])
            error_count = int(parts[1].split(": ")[1])
            ARE = float(parts[2].split(": ")[1])
            no_error_counts.append(no_error_count)
            error_counts.append(error_count)
            AREs.append(ARE)

    # 输出测试结果的平均值
    print(f"average no_error_count: {np.mean(no_error_counts)}")
    print(f"average error_count: {np.mean(error_counts)}")
    print(f"average ARE: {np.mean(AREs)}")

    print(f"max no_error_count: {np.max(no_error_counts)}")
    print(f"max error_count: {np.max(error_counts)}")
    print(f"max ARE: {np.max(AREs)}")

    # 绘制CDF图
    plot_cdf(AREs, "ARE CDF", "ARE", "CDF", "ARE_cdf.png")
    plot_cdf(no_error_counts, "no_error_count CDF", "no_error_count", "CDF", "no_error_count_cdf.png")
    plot_cdf(error_counts, "error_count CDF", "error_count", "CDF", "error_count_cdf.png")