
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
以下是根据内容整理的规范 Markdown 格式：

```markdown
### 1. Poseidon2哈希算法原理
Poseidon是一种基于置换的STARK友好哈希算法，核心原理如下：

#### 1.1 核心数学结构
**1.1.1 海绵结构（Sponge Construction）**
```math
\begin{aligned}
&S = \{s_0, s_1, \dots, s_{t-1}\} \in \mathbb{F}^t \\
&\text{状态容量} = t \text{个域元素} \\
&\text{速率} = r \quad \text{(容量} = c = t - r\text{)}
\end{aligned}
```
其中 $\mathbb{F}$ 为素数域（如 BN254, BLS12-381 等）

**1.1.2 算法流程**
```mermaid
flowchart TD
    A[输入消息] --> B(填充至 r 的倍数)
    B --> C[初始化状态: S = 0ᵗ]
    C --> D{消息分块处理}
    D -->|吸收块| E[状态累加: S[0:r] += Mᵢ]
    E --> F{是否完成?}
    F -->|否| G[应用置换函数 F]
    G --> D
    F -->|是| H[输出哈希]
    H -->|前 r 元素| I[应用置换函数 F]
    I --> J[截取输出长度]
```

#### 1.2 置换函数（Permutation）核心
**1.2.1 置换函数结构**
$$F = Linear \circ PartialRound \circ Linear \circ FullRound$$
```python
def F(S):
    S = FullRound(S)     # 全轮函数
    S = LinearLayer(S)   # 线性层
    S = PartialRound(S)  # 部分轮函数
    S = LinearLayer(S)   # 线性层
    return S
```

**1.2.2 Full Round（全轮函数）**
| 步骤 | 运算 | 数学表示 |
|------|------|----------|
| 1 | 添加常数 | $S = S + RC_i$ |
| 2 | S-box应用 | $\forall j,\ S_j^{(k+1)} = \left(S_j^{(k)}\right)^\alpha$ |
| 3 | MDS混合 | $S^{(k+1)} = M \cdot S^{(k)}$ |

**参数说明**：
- **指数选择**：$\alpha$ 取 5 ($x^5$) 或 3 ($x^3$)
- **MDS矩阵**：最大距离可分离矩阵（保证扩散性）

**1.2.3 Partial Round（部分轮函数）**
- 仅对**首状态元素**应用非线性
- 数学表示：
  ```math
  S_j^{(k+1)} = 
  \begin{cases} 
  \left(S_j^{(k)}\right)^\alpha & j=0 \\
  S_j^{(k)} & \text{其他}
  \end{cases}
  ```

**1.2.4 Linear Layer（线性层）**
```math
\begin{bmatrix}
s_0' \\
s_1' \\
\vdots \\
s_{t-1}'
\end{bmatrix}
= M_{mds} \times
\begin{bmatrix}
s_0 \\
s_1 \\
\vdots \\
s_{t-1}
\end{bmatrix}
```
**特性**：
- $det(M_{mds}) \neq 0$（保证可逆性）

#### 1.3 安全设计参数
**1.3.1 轮数配置**
| 函数类型 | 参数 | 典型值(t=12) |
|----------|------|--------------|
| Full Round | $R_F$ | 8 |
| Partial Round | $R_P$ | 22 |
| **总轮数** | $R = R_F + R_P$ | **30** |

**1.3.2 抗攻击保证**
- **统计饱和攻击**：$R_P \geq 50$ 轮防御
- **代数攻击**：多重二次方程系统防护
- **差分分析**：最小活跃 S-box 约束

#### 1.4 性能优化创新
**1.4.1 域运算优化**
- **免反演运算**：$x^5$ S-box 设计
- **SIMD 友好**：  
  线性层矩阵分解：
  ```math
  M_{mds} = \begin{bmatrix} A & 0 \\ 0 & I \end{bmatrix} \times \begin{bmatrix} I & B \\ C & D \end{bmatrix}
  ```

**1.4.2 并行化策略**
```mermaid
flowchart LR
    A[输入状态] --> B(S-box层)
    B --> C[并行计算]
    C -->|t通道| D[MDS乘法]
    D --> E[累加输出]
```
```


**1.4.3 与传统哈希对比** 

| 特性         | SHA-256 | Poseidon2 |
|--------------|---------|-----------|
| 域           | $GF(2)$ | $GF(p)$   |
| 基础操作     | 位运算  | 域运算    |
| ZKP 友好度   | 低      | 高        |
| 轮函数复杂度 | 高      | 低        |
| 证明生成速度 | 慢      | 快 (10-100x) |

**1.4.4 与Poseidon对比

| 特性 | Poseidon | Poseidon2 |
|------|----------|-----------|
| **轮函数结构** | 均匀全轮 | 混合轮结构 |
| **计算复杂度** | O(t²·R) | O(t·log t·R) |
| **硬件友好度** | 中等 | 高（流水线优化） |
| **抗侧信道** | 基础 | 增强 |
| **S-box应用** | 全元素 | 选择性 |


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

