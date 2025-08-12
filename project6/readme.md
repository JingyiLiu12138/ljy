## project6
# Google Password Checkup验证
来自刘巍然老师的报告  google password checkup，参考论文 https://eprint.iacr.org/2019/723.pdf 的 section 3.1 ，也即 Figure 2 中展示的协议，尝试实现该协议，（编程语言不限）。

## 1. 实验背景
本实验实现论文《Private Intersection-Sum Protocol with Applications to Attributing Aggregate Ad Conversions》[1]中提出的私有交集求和协议(DDH-based Private Intersection-Sum)。该协议允许多方安全计算交集和对应数据的加和，同时保护非交集数据的隐私，应用于Google Password Checkup等场景。

## 2. 协议原理（Section 3.1, Figure 2）
协议涉及两方：
- **P1**：持有元素集合 `V = {v₁, ..., vₙ}`
- **P2**：持有键值对集合 `{(w₁, t₁), ..., (wₘ, tₘ)}`

协议目标：
1. 计算交集元素数量 `|V ∩ W|`
2. 计算交集对应值的加和 `∑{tᵢ : wᵢ ∈ V}`
3. 不泄露交集外的其他信息

核心密码学组件：
- **椭圆曲线**：使用NIST P-256曲线实现DDH假设
- **Paillier加密**：实现同态加法运算
- **双线性映射**：通过两次指数运算实现安全比较

## 3. 实验实现

### 3.1 依赖库
```python
import random
import hashlib
from ecdsa import NIST256p
from ecdsa.ellipticcurve import PointJacobi
from phe import paillier  # 加法同态加密库
```
### 3.2 核心类实现
```python
class DDHPrivateIntersectionSum:
    def __init__(self, p1_data, p2_data):
        # 初始化椭圆曲线参数
        self.curve = NIST256p.curve
        self.G = NIST256p.generator
        self.n = NIST256p.order
        
        # 生成加密密钥
        self.k1 = random.randint(1, self.n - 1)  # P1私钥
        self.k2 = random.randint(1, self.n - 1)  # P2私钥
        self.paillier_pub, self.paillier_priv = paillier.generate_paillier_keypair(n_length=768)
        
        # 存储数据
        self.p1_data = p1_data
        self.p2_data = p2_data

    def round1_p1(self):
        """P1: 计算H(v_i)^k1并发送（随机排序）"""
        processed_points = []
        for v in self.p1_data:
            point = self.hash_to_point(v)
            exp_point = self.k1 * point  # g^{k1}
            processed_points.append(exp_point)
        return self.shuffle_list(processed_points)

    def round2_p2(self, p1_points):
        """P2: 
        1. 双加密P1的点 (g^{k1k2})
        2. 准备加密数据集 (g^{k2}, Enc(t))
        """
        # 双加密
        dual_enc_points = [self.k2 * p for p in p1_points]
        
        # 准备P2数据
        p2_enc_points = []
        p2_enc_values = []
        for w, t_val in self.p2_data:
            point = self.hash_to_point(w)
            exp_point = self.k2 * point
            enc_t = self.paillier_pub.encrypt(t_val)
            p2_enc_points.append(exp_point)
            p2_enc_values.append(enc_t)
        
        # 洗牌保持对应关系
        combined = list(zip(p2_enc_points, p2_enc_values))
        random.shuffle(combined)
        p2_enc_points, p2_enc_values = zip(*combined)
        
        return (self.shuffle_list(dual_enc_points), 
                list(p2_enc_points), 
                list(p2_enc_values))

    def round3_p1(self, dual_enc_points, p2_points, p2_enc_values):
        """P1: 检测交集并计算同态和"""
        valid_indices = []
        for i, p2_point in enumerate(p2_points):
            dual_p2_point = self.k1 * p2_point
            if dual_p2_point in dual_enc_points:
                valid_indices.append(i)
        
        # 同态求和
        sum_ciphertext = self.paillier_pub.encrypt(0)
        for idx in valid_indices:
            sum_ciphertext += p2_enc_values[idx]
            
        self.intersection_size = len(valid_indices)
        return sum_ciphertext

    def final_output_p2(self, sum_ciphertext):
        """P2: 解密获得最终结果"""
        intersection_sum = self.paillier_priv.decrypt(sum_ciphertext)
        return self.intersection_size, intersection_sum

    # 辅助函数
    def hash_to_point(self, input_str):
        h = hashlib.sha256(input_str.encode()).digest()
        h_int = int.from_bytes(h, 'big') % self.n
        if h_int == 0: h_int = 1
        return h_int * self.G
    
    def shuffle_list(self, input_list):
        shuffled = input_list[:]
        random.shuffle(shuffled)
        return shuffled
```
## 4.测试结果

测试数据示例为
<img width="1049" height="102" alt="image" src="https://github.com/user-attachments/assets/26a2d5de-771a-4bdf-a8ae-a994cc0026ae" />
由图可得，交集为id2，id3，id5，交集和总值为10+20+40=70，结果正确
<img width="1621" height="285" alt="image" src="https://github.com/user-attachments/assets/232e8535-08f8-4009-b5fe-d07cb330d165" />

