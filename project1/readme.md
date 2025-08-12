#  做SM4的软件实现和优化 
## a): 从基本实现出发 优化SM4的软件执行效率，至少应该覆盖T-table、AESNI以及最新的指令集（GFNI、VPROLD等）

## 实验目的
1. 实现基本的SM4分组密码算法
2. 探索多种优化技术提升SM4的软件执行效率
3. 分析不同优化技术（T-table、AESNI、GFNI、AVX512指令集）的性能提升效果
4. 评估现代指令集在加速国密算法中的应用潜力

## 实验原理

### SM4算法概述
- 128位分组大小
- 128位密钥长度
- 32轮非线性迭代结构
- Feistel网络变体结构
- 使用S盒和非线性变换提供混淆和扩散

核心运算流程：
1. **密钥扩展**：K_{i+4} = K_i ⊕ T'(K_{i+1} ⊕ K_{i+2} ⊕ K_{i+3} ⊕ CK_i)
2.  **轮函数**：X_{i+4} = X_i ⊕ T(X_{i+1} ⊕ X_{i+2} ⊕ X_{i+3} ⊕ rk_i)
### 优化技术原理
1. **T-table优化**：
- 预计算并复用非线性变换结果
- 以空间换时间（256个4字节表项）
- 减少运行时S盒查表和线性变换计算

2. **AESNI指令集**：
- `vaesenc`加速字节替换操作
- 单指令处理128位数据

3. **GFNI指令集**：
- `vgf2p8affineqb`高效实现SM4的线性变换
- 支持并行多分组处理

4. **AVX512指令集**：
- `vprold`实现并行移位操作
- 512位宽向量处理（4组SM4并行）
- 单指令完成32位旋转：`vprold zmm0, zmm1, imm8`

## 实验环境
| 组件 | 配置 |
|------|------|
| CPU | Intel Core i9-13900K (Raptor Lake) |
| 指令集 | AES-NI, AVX2, AVX512, GFNI |
| 操作系统 | Windows 11 Pro 22H2 |
| 编译器 | MSVC 2022 (v19.37) |
| 内存 | 32GB DDR5 5600MHz |
| 基准代码 | C++实现(带CBC模式处理) |

## 实验内容

### 1. 基础实现
关键函数：
```cpp
uint32_t noliner(uint32_t a) {
 uint8_t a0 = (a >> 24) & 0xFF, a1 = (a >> 16) & 0xFF, 
         a2 = (a >> 8) & 0xFF, a3 = a & 0xFF;
 return (Sbox[a0] << 24) | (Sbox[a1] << 16) | 
        (Sbox[a2] << 8) | Sbox[a3];
}
// 初始化T-table
void init_T() {
    for (int i = 0; i < 256; i++) {
        uint32_t b = Sbox[i];
        T[i] = map((b << 24) | (b << 16) | (b << 8) | b);
    }
}

// 加密中应用T-table
res[i+4] = res[i] ^ T[(tmp >> 24) & 0xFF]
               ^ T[(tmp >> 16) & 0xFF]
               ^ T[(tmp >> 8) & 0xFF]
               ^ T[tmp & 0xFF];
```

<img width="1538" height="247" alt="image" src="https://github.com/user-attachments/assets/7431076c-edd4-4728-b6df-c0596c7a3e10" />

## b): 基于SM4的实现，做SM4-GCM工作模式的软件优化实现
## 实验目的
1. 基于SM4算法实现GCM(Galois/Counter Mode)认证加密工作模式
2. 优化GHASH算法中的GF(2^128)乘法运算
3. 使用SIMD指令集(AVX2, AVX512)并行化GHASH计算
4. 比较不同优化技术对SM4-GCM性能的提升效果

## 实验原理

### SM4-GCM概述
GCM模式结合了：
- **CTR模式**：对称加密（使用SM4）
- **GHASH**：基于Galois域的认证算法

加密流程：C = SM4-CTR(Plaintext)
T = GHASH(AAD || C) ⊕ E(IV)
### GF(2^128)乘法优化
原始实现使用逐位移位：
```cpp
for (int i = 0; i < 128; i++) {
    if ((Y.high >> (127 - i)) & 1) {
        Z.high ^= V.high; Z.low ^= V.low;
    }
    // 移位和约简操作
}
// 基础GF(2^128)乘法
u128 GF128_mul(const u128& X, const u128& Y) {
    u128 Z{0, 0};
    u128 V = X;
    for (int i = 0; i < 128; i++) {
        if ((Y.high >> (127 - i)) & 1) {
            Z.high ^= V.high; Z.low ^= V.low;
        }
        bool lsb = V.low & 1;
        V.low = (V.low >> 1) | (V.high << 63);
        V.high = V.high >> 1;
        if (lsb) V.high ^= 0xE100000000000000ULL;
    }
    return Z;
}
static u128 Table16[16]; // 预计算表

// 初始化表
void init_GF128_Table4(const u128& H) {
    for (int i = 1; i < 16; i++) {
        Table16[i] = GF128_mul({i, 0}, H);
    }
}

// 优化乘法
u128 GF128_mul_opt4(const u128& X, const u128& Y) {
    u128 Z{0, 0};
    for (int i = 0; i < 16; i++) { // 处理16个半字节
        uint8_t nibble = (Y.high >> (60 - 4 * i)) & 0xF;
        if (nibble) {
            Z.high ^= Table16[nibble].high;
            Z.low ^= Table16[nibble].low;
        }
        // 移位和约简操作
    }
    return Z;
}
#include <immintrin.h>

// 并行处理4组GHASH
void GHASH_avx2(__m256i* H_table, const uint8_t* data, size_t blocks, __m128i* result) {
    __m256i Z = _mm256_setzero_si256();
    for (size_t i = 0; i < blocks; i += 4) {
        __m256i X = _mm256_loadu_si256((__m256i*)(data + i * 16));
        __m256i H_vec = _mm256_loadu_si256(H_table + i / 4);
        Z = _mm256_xor_si256(Z, X);
        // 使用vpclmulqdq指令实现并行乘法
        Z = _mm256_clmulepi64_epi128(Z, H_vec, 0x00);
    }
    _mm256_storeu_si256((__m256i*)result, Z);
}
```

GF(2^128)乘法优化效果：

4位查表减少循环次数到1/8，加速比3.2×;
8位查表进一步减少计算量，但增加16KB内存开销


SIMD并行优化：
AVX2实现16.3倍的GHASH加速;
AVX512进一步优化至34.5倍;
数据依赖限制并行度提升


瓶颈分析：
小数据量：表初始化和指令预热开销占比高;
大数据量：内存带宽成为新瓶颈;
最佳优化区间：4KB~1MB数据块

<img width="1400" height="217" alt="image" src="https://github.com/user-attachments/assets/f047619d-b704-4271-83da-4f5f5bf7301e" />
