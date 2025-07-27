##  project5：SM2的软件实现优化 
a). 考虑到SM2用C 语言来做比较复杂，大家看可以考虑用python来做 sm2的 基础实现以及各种算法的改进尝试


b). 20250713-wen-sm2-public.pdf 中提到的关于签名算法的误用 分别基于做poc验证，给出推导文档以及验证代码


c). 伪造中本聪的数字签名
<img width="2680" height="903" alt="image" src="https://github.com/user-attachments/assets/88a06dd4-640e-4d06-9d34-c63be1c40586" />


可以考虑尝试蒙哥马利、点乘算法优化以及并行运算优化等等优化措施：
点乘算法优化：
''' python
def naf_window_mult(k, point, a, p, w=5):
    # 预计算表
    table = [None] * (1 << (w-1))
    table[0] = point
    for i in range(1, 1 << (w-1)):
        table[i] = point_add(table[i-1], point, a, p)
    
    # NAF转换
    naf = []
    while k:
        if k & 1:
            t = 2 - (k % 4)
            k -= t
            naf.append(t)
        else:
            naf.append(0)
        k //= 2
    
    # NAF计算
    result = (0, 0)
    for i in reversed(naf):
        result = point_add(result, result, a, p)
        if i > 0:
            result = point_add(result, table[i//2], a, p)
        elif i < 0:
            result = point_add(result, neg_point(table[-i//2], p), a, p)
    return result
'''

集成优化之后的结果
<img width="2518" height="679" alt="image" src="https://github.com/user-attachments/assets/f9bdec8f-713c-41d7-8a26-724f367055a0" />

## b
### 1）相同用户重用随机数k

### 2）不同用户使用相同k

### 3）与ECDSA公用（d，k）

### 4）k值泄漏
代码验证得到，四个签名误用都会导致密钥泄露
<img width="1323" height="1285" alt="image" src="https://github.com/user-attachments/assets/b90b88b7-3f88-4c99-9d3c-b4f512c0876d" />

## c Satoshi签名伪造

