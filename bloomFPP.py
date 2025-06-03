import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 固定参数
n = 120000
i_vals = np.arange(2, n)  # 向量化的 i 值

# 向量化 FPP 计算函数
def compute_fpp_vectorized(k, m):
    p_vals = (1 - np.exp(-(i_vals - 1) / m)) ** k
    return np.sum(p_vals) / n

def compute_fpp_vectorized_bloom(k, m):
    p_vals = (1 - np.exp(-(i_vals - 1)*k / m)) ** k
    return np.sum(p_vals) / n


# 设置参数范围
k_values = np.arange(1, 21, 1)
# m_values = np.arange(100000, 300001, 1000)
m_values = np.arange(100000, 200001, 10000)
K, M = np.meshgrid(k_values, m_values*3)
for m_i in m_values:
    print("m_i: ",m_i)
    cm_ffp = compute_fpp_vectorized(3,m_i)
    print("cm_ffp: ",cm_ffp)

    bloom_ffp=compute_fpp_vectorized_bloom(3,3*m_i)
    print("bloom_ffp: ",bloom_ffp)

# 初始化数组
FPP = np.zeros_like(K, dtype=float)
KM_product = np.zeros_like(K, dtype=float)

# 计算 FPP 并记录 k*m（不满足条件则设为无穷大）
for i in range(K.shape[0]):
    for j in range(K.shape[1]):
        k = K[i, j]
        m = M[i, j]
        fpp = compute_fpp_vectorized_bloom(k, m)
        FPP[i, j] = fpp
        if fpp < 0.05:
            KM_product[i, j] = m
        else:
            KM_product[i, j] = np.inf

# 查找最小 k*m 且 FPP < 1% 的组合
min_index = np.unravel_index(np.argmin(KM_product), KM_product.shape)
print(min_index)
optimal_k = int(K[min_index])
optimal_m = int(M[min_index])
optimal_fpp = FPP[min_index]
optimal_km = int(KM_product[min_index])


# plt.tight_layout()
# plt.show()
# 打印结果
print(f"Optimal k: {optimal_k}")
print(f"Optimal m: {optimal_m}")
print(f"Optimal FPP: {optimal_fpp:.4f}")

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制带透明度的表面
surf = ax.plot_surface(K, M, FPP, cmap='viridis', alpha=0.9, antialiased=True)

# 红色柱线（更粗更醒目）
ax.plot([optimal_k, optimal_k], [optimal_m, optimal_m],
        [0, optimal_fpp], color='red', linewidth=3)

# 最优点标记（大红点）
ax.scatter(optimal_k, optimal_m, optimal_fpp, color='red', s=100, marker='o', depthshade=False)

# 文本标注（透明背景）
ax.text(optimal_k, optimal_m, optimal_fpp + 0.002,
        f'k={optimal_k}\nm={optimal_m}\nFPP={optimal_fpp:.4f}',
        color='black', fontsize=10,
        bbox=dict(facecolor='white', edgecolor='black', alpha=0.1, boxstyle='round,pad=0.4'))

# 标签设置
ax.set_xlabel('k (number of hash functions)')
ax.set_ylabel('m (number of bits)')
ax.set_zlabel('FPP (Flow False Positive)')
ax.set_title('Min k*m with FPP < 1% (n=150000)')

plt.tight_layout()
plt.show()
