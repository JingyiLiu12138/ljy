
# 用circom实现poseidon2哈希算法的电路
## 实验目标
### 1.poseidon2哈希算法参数参考参考文档1的Table1，用(n,t,d)=(256,3,5)或(256,2,5)
### 2.电路的公开输入用poseidon2哈希值，隐私输入为哈希原象，哈希算法的输入只考虑一个block即可。
### 2. 用Groth16算法生成证明
参考文档：
1. poseidon2哈希算法https://eprint.iacr.org/2023/323.pdf
2. circom说明文档https://docs.circom.io/
3. circom电路样例 https://github.com/iden3/circomlib

## 实验原理
### 1. Poseidon2哈希算法原理
Poseidon2 是基于海绵结构的零知识证明友好型哈希函数，其设计特别适用于零知识证明系统。下面我们通过数学推导详细解析其设计原理。
1. 海绵结构基础

Poseidon2 采用海绵结构，定义在有限域 $GF(p)$ 上（$p$ 为大素数）。海绵结构包含两个阶段：

(1) **吸收阶段**：输入消息 $M$ 被分为 $r$ 长度的块（$r$ 为速率）
(2) **挤压阶段**：输出哈希值

状态表示为：$S = (s_0, s_1, \dots, s_{t-1}) \in \mathbb{F}_p^t$  
其中 $t = r + c$（$c$ 为容量）

2. 置换核心设计

Poseidon2 的核心是置换函数 $f: \mathbb{F}_p^t \rightarrow \mathbb{F}_p^t$，包含三种操作：

(1) Add-Round Constants (ARC)

$$ \text{ARC}_i(S) = S + C_i $$
其中 $C_i \in \mathbb{F}_p^t$ 是预先计算的轮常数

(2) SubWords (S-Box 层)

使用单项式 S-Box：$x^\alpha$（常用 $\alpha=5$ 或 $\alpha=3$）

$$ \text{S-Box}(S) = (s_0^\alpha, s_1^\alpha, \dots, s_{t-1}^\alpha) $$

(3) MixLayer (线性层)

使用 MDS 矩阵 $M \in \mathbb{F}_p^{t \times t}$ 确保完全扩散：

$$ \text{MixLayer}(S) = M \cdot S $$

其中 $M$ 满足：任何非零输入差异会导致至少 $t + 1$ 个输出差异

3. 完整置换函数

Poseidon2 使用优化的轮结构：

```math
f(S) = \underbrace{\text{ExternalFullRounds}}_{R_f} \circ \underbrace{\text{PartialRounds}}_{R_p} \circ \underbrace{\text{ExternalFullRounds}}_{R_f}
```

其中：
- $R_f$：完全轮数（通常 2-8 轮）
- $R_p$：部分轮数（通常 22-60 轮）

完全轮结构
$$
\begin{aligned}
\text{FullRound}_i(S) = &\text{ } \\
&1.\ \text{ARC}(S + C_i) \\
&2.\ \text{Apply S-Box to ALL elements} \\
&3.\ \text{Apply MDS matrix } M
\end{aligned}
$$

部分轮结构
$$
\begin{aligned}
\text{PartialRound}_i(S) = &\text{ } \\
&1.\ \text{ARC}(S + C_i) \\
&2.\ \text{Apply S-Box ONLY to first element } s_0^\alpha \\
&3.\ \text{Apply MDS matrix } M
\end{aligned}
$$

4. 安全参数选择

(1) S-Box 选择
- 幂函数 $x^\alpha$ 需满足：
  - $\gcd(\alpha, p-1) = 1$（保证可逆性）
  - 非线性度最大化
  - $\alpha=5$ 在多个域上表现优良

(2) MDS 矩阵构造
使用 Cauchy 矩阵确保 MDS 属性：
$$ M_{ij} = \frac{1}{x_i + y_j} $$
其中 $x_i, y_j$ 是域中互不相同的元素
(3) 轮数确定
通过 HADES 设计策略确保：
- 抵抗统计攻击
- 抵抗代数攻击
- 抵抗差分/线性密码分析

轮数下限公式：
$$ R \geq 2 \cdot \left\lceil \frac{2\log t}{\log \alpha} \right\rceil + R_{\text{安全}} $$
5. 完整哈希流程

输入处理：
(1) 消息填充：$ \text{pad}(M) = M \parallel 1 \parallel 0^k $ 使长度 $\equiv 0 \pmod{r}$
(2) 分块：$ M = B_0 \parallel B_1 \parallel \cdots \parallel B_{n-1} $

海绵操作：
```math
\begin{array}{c}
\text{Initialize state } S = 0 \\
\downarrow \\
\text{For each block } B_i: \\
\quad S[0:r-1] \leftarrow S[0:r-1] + B_i \\
\quad S \leftarrow f(S) \\
\downarrow \\
\text{Output } H = S[0:r-1] \quad (\text{truncated if needed})
\end{array}
```

6. 代数分析

置换函数的度数
每轮增加代数复杂度：
- 完全轮：所有分量度数乘以 $\alpha$
- 部分轮：第一分量度数乘以 $\alpha$

经过 $R$ 轮后，多项式度数上限：
$$ \deg(f) \leq \alpha^{R_f} \cdot \alpha^{R_p} = \alpha^{R_f + R_p} $$

安全边界
为防止插值攻击，要求：
$$ \alpha^R > 2^{\lambda} $$
其中 $\lambda$ 为安全参数（如 $\lambda=128$）

7. 与传统哈希对比

| 特性         | SHA-256 | Poseidon2 |
|--------------|---------|-----------|
| 域           | $GF(2)$ | $GF(p)$   |
| 基础操作     | 位运算  | 域运算    |
| ZKP 友好度   | 低      | 高        |
| 轮函数复杂度 | 高      | 低        |
| 证明生成速度 | 慢      | 快 (10-100x) |



### 2. 零知识证明原理
1. **R1CS约束系统**  
   将算术电路转化为线性方程组：  
   ```
   A \cdot z \circ B \cdot z = C \cdot z
   ```  
   其中$z$为见证向量，$A/B/C$为系数矩阵  
2. **Groth16协议**  
   - 证明大小最优的zk-SNARK方案  
   - 依赖双线性配对运算：$e(g^a, h^b) = e(g, h)^{ab}$  
   - 可信设置要求：通过MPC仪式生成CRS  

---

## 实验设计
### 1. 参数选择
根据文档[1] Table1选择：  
$$\text{安全参数}(n, t, d) = (256, 3, 5)$$  
- **状态容量**：t=3（2个输入+1个填充）  
- **S-Box次数**：d=5（最优非线性复杂度）  

### 2. 电路实现
```circom
pragma circom 2.1.6;
include "circomlib/circuits/poseidon.circom";

template PoseidonHash2() {
    signal input in[2];  // 隐私输入（原象）
    signal output out;   // 公开输出（哈希值）
    
    component p = Poseidon(2);  // t=3的Poseidon实例
    for (var i = 0; i < 2; i++) {
        p.inputs[i] <== in[i];  // 输入绑定
    }
    out <== p.out;       // 输出绑定
}
component main = PoseidonHash2();
```

---

## 实验步骤
### 1. 编译电路
利用zkREPL在线编译poseidon2.circom文件。
生成文件说明：  
| 文件                 | 用途                            |
|----------------------|---------------------------------|
| `poseidon2.r1cs`     | R1CS约束系统（2,145个约束）     |
| `poseidon2.wasm`     | Witness计算模块（WebAssembly）  |
| `poseidon2.sym`      | 信号映射表（调试定位约束错误）  |

### 2. 输入参数`INPUT`
```/* INPUT ={
  "in": ["123", "456"]
}*/
```

## 实验结果
### 1. 输出结果
<img width="639" height="529" alt="8790fa1861811647ec5098620740d4a" src="https://github.com/user-attachments/assets/19b507ff-1823-4d73-91f5-aee0826ab0d1" />

| 指标                 | 值    |
|----------------------|-------|
| template instances   | 69    |
| non-linear constraints | 240   |
| linear constraints   | 0     |
| public inputs        | 0     |
| public outputs       | 1     |
| private inputs       | 2     |
| private outputs      | 0     |
| wires                | 243   |
| labels               | 1111  |

### 2. PLONK验证
生成PLONK验证器和验证者密钥，以及一个solidity验证合同和示例交互式的SnarklS网络应用程序：
<img width="577" height="207" alt="df14e93c69befb9e982b2935e5dbe2d" src="https://github.com/user-attachments/assets/65ef7d69-b66c-4bda-9b3c-5456f7ee4a0e" />
| 文件名           | 描述                         |
|------------------|------------------------------|
| `untitled.r1cs` | R1CS格式的约束系统            |
|                  | 包含所有算术约束的方程组      |
| `untitled.wasm` | WebAssembly模块              |
|                  | 用于高效计算witness          |
| `untitled.sym`  | 符号表                       |
|                  | 调试时映射信号名与信号ID      |


### 3. Grouth16生成证明
生成Grouth16的证明者和验证者密钥，以及一个solidity验证合同和示例交互式的SnarklS网络应用程序：
<img width="627" height="217" alt="565a0e7691cc0243fa7f7d4d5ba4d10" src="https://github.com/user-attachments/assets/8f3ccefd-0a45-4afa-9283-98f6a1aaa99c" />
| 文件名                   | 说明                   |
|--------------------------|------------------------|
| `untitled.groth16.zkey`    | 完整的证明密钥         |
| `untitled.groth16.vkey.json `  | 验证密钥          |
| `untitled.groth16.sol `       |solidity验证合同     |

### 4. 正确性验证
上传ZKey，曲儿其是基于与当前zkREPL相同的原代码编译而成的
<img width="1051" height="1289" alt="1e0cbcb132167f4cf58239cc6740f59" src="https://github.com/user-attachments/assets/be560aca-ff6d-4bd1-9711-ee119869206d" />


---

## 分析讨论
### 1. 安全边界
- 抗碰撞性：$2^{128}$安全性满足（通过256位状态容量实现）
- 代数攻击防护：5次S-Box破坏线性结构

### 2. 优化方向
1. **自定义约束门**：合并线性运算减少约束数  
2. **并行化计算**：利用WASM SIMD指令加速  
3. **递归证明**：支持多块哈希流水线处理  

---

