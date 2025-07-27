import math
import random


def hash(m):
    """简单的哈希函数实现（用于演示）"""
    return int.from_bytes(m.encode(), byteorder='big') % 19


def mul_inv(a, m):
    if math.gcd(a, m) != 1:
        return None
    return pow(a, -1, m)


def add(m, n):
    if m == 0:
        return n
    if n == 0:
        return m
    if m != n:
        if math.gcd(m[0] - n[0], p) != 1:
            return 0
        k = ((m[1] - n[1]) * mul_inv(m[0] - n[0], p)) % p
    else:
        k = ((3 * (m[0] * m[0]) + a) * mul_inv(2 * m[1], p)) % p
    x = (k * k - m[0] - n[0]) % p
    y = (k * (m[0] - x) - m[1]) % p
    return [x, y]


def p_mul_n(n, p):
    if n == 1:
        return p
    tmp = p
    while n >= 2:
        tmp = add(tmp, p)
        n -= 1
    return tmp


def ECDSA_sign(m, n, G, d, k):
    R = p_mul_n(k, G)
    r = R[0] % n
    e = hash(m)
    s = (mul_inv(k, n) * (e + d * r)) % n
    return r, s


def ECDSA_ver(m, n, G, r, s, P):
    e = hash(m)
    w = mul_inv(s, n)
    if w is None:
        return False
    v1 = (e * w) % n
    v2 = (r * w) % n
    w_point = add(p_mul_n(v1, G), p_mul_n(v2, P))
    return (w_point != 0) and (w_point[0] % n == r)


def ver_no_m(e, n, G, r, s, P):
    w = mul_inv(s, n)
    if w is None:
        print("失败：s的逆元不存在")
        return False
    v1 = (e * w) % n
    v2 = (r * w) % n
    w_point = add(p_mul_n(v1, G), p_mul_n(v2, P))
    if w_point == 0:
        print('失败')
        return False
    success = w_point[0] % n == r
    print('成功' if success else '失败')
    return success


def pretend(n, G, P):  # satoshi无消息签名算法
    u = random.randint(1, n - 1)
    v = random.randint(1, n - 1)
    print(f"随机参数: u={u}, v={v}")

    R_point = add(p_mul_n(u, G), p_mul_n(v, P))
    if R_point == 0:
        print("失败：零元素")
        return
    R = R_point[0] % n

    v_inv = mul_inv(v, n)
    if v_inv is None:
        print("失败：v的逆元不存在")
        return

    e1 = (R * u * v_inv) % n
    s1 = (R * v_inv) % n

    print(f"伪造签名: e1={e1}, r={R}, s1={s1}")

    # 验证伪造的签名
    print("伪造签名验证结果:", end=' ')
    ver_no_m(e1, n, G, R, s1, P)


# 椭圆曲线参数
a = 2
b = 3
p = 17
G = [6, 9]
n = 19
d = 5
P = p_mul_n(d, G)  # 公钥

# 运行伪造攻击
print("尝试伪造中本聪数字签名:")
pretend(n, G, P)