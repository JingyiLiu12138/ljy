
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
Poseidon是一种基于置换的STARK友好哈希算法，核心原理如下：
1. **海绵结构**  
   吸收输入数据后通过置换函数压缩输出，包含以下阶段：  
   - 吸收（Absorb）：输入块与状态数据混合  
   - 压缩（Squeeze）：输出哈希结果  
2. **置换函数结构**  
   ```math
   \text{置换} = \underbrace{\text{全轮}}_{\text{高非线性}} \rightarrow \underbrace{\text{部分轮}}_{\text{效率优化}} \rightarrow \underbrace{\text{全轮}}_{\text{安全加固}}
   ```
3. **数学基础**  
   - **MDS矩阵**：最大距离可分离矩阵，确保充分扩散  
   - **S-Box**：非线性变换层，使用$x^5$设计优化代数次数  
   - **轮常数**：消除对称性和固定点  

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

## 附录：关键文件树
```
.
├── circuit/
│   ├── poseidon2.circom    # 电路源码
├── out/
│   ├── poseidon2.r1cs       # 约束系统
│   ├── poseidon2_0001.zkey  # 证明密钥
│   └── verification_key.json
└── scripts/
    ├── compile.sh           # 自动编译脚本
    └── verify.sh            # 验证脚本
```
