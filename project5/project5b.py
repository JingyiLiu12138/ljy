import math
import hashlib


# 辅助函数：生成椭圆曲线签名所需的整数e
def generate(m, n):
    tmp = hashlib.sha256(m.encode()).digest()
    return int.from_bytes(tmp, 'big') % n


# 辅助函数：计算a在模m下的乘法逆元
def mul_inv(a, m):
    if math.gcd(a, m) != 1:
        return None
    return pow(a, -1, m)


# 椭圆曲线点加法
def ec_add(P, Q):
    if P == 0 or P is None:
        return Q
    if Q == 0 or Q is None:
        return P

    x1, y1 = P
    x2, y2 = Q

    # 点不同
    if x1 != x2:
        denominator = x2 - x1
        if math.gcd(denominator, p) != 1:
            return None
        k = (y2 - y1) * mul_inv(denominator, p) % p
    # 点相同（点加倍）
    else:
        numerator = 3 * x1 * x1 + a
        denominator = 2 * y1
        if math.gcd(denominator, p) != 1:
            return None
        k = numerator * mul_inv(denominator, p) % p

    x3 = (k * k - x1 - x2) % p
    y3 = (k * (x1 - x3) - y1) % p
    return (x3, y3)


# 椭圆曲线标量乘法
def ec_mul(n, P):
    result = None
    current = P

    while n:
        if n & 1:
            result = ec_add(result, current)
        current = ec_add(current, current)
        n >>= 1

    return result


# ECDSA签名生成
def ecdsa_sign(n, G, d, k, e):
    R = ec_mul(k, G)  # 临时公钥R=k*G
    if R is None:
        return None, None
    r = R[0] % n
    s = (mul_inv(k, n) * (e + d * r)) % n
    return r, s


# Schnorr签名生成
def schnorr_sign(m, n, G, d, k):
    R = ec_mul(k, G)  # 临时公钥计算
    if R is None:
        return None, None, None
    e_val = generate(str(R[0]) + m, n)  # 挑战值计算
    s = (k + e_val * d) % n
    return R[0], s, e_val


# 1. 相同用户重用随机数k (ECDSA)
def scenario1_reuse_k():
    print("\n1. 相同用户重用随机数k (ECDSA)")
    r1, s1 = ecdsa_sign(n, G, d1, k, e1)
    r2, s2 = ecdsa_sign(n, G, d1, k, e2)

    # 验证签名是否成功
    if r1 is None or r2 is None:
        print("错误：签名生成失败")
        return

    # 恢复nonce k
    denominator = (s1 - s2) % n
    inv_denom = mul_inv(denominator, n)
    if inv_denom is None:
        print("错误：无法计算分母的模逆元")
        return

    k_rec = (e1 - e2) * inv_denom % n

    # 恢复私钥d
    r_inv = mul_inv(r1, n)
    if r_inv is None:
        print("错误：无法计算r的模逆元")
        return

    d_rec = (s1 * k_rec - e1) * r_inv % n

    print(f"原私钥 d1: {d1}")
    print(f"恢复的私钥 d1: {d_rec}")
    print(f"恢复的nonce k: {k_rec}")
    print("验证结果:", "成功" if d_rec == d1 else "失败")


# 2. 不同用户使用相同k (ECDSA)
def scenario2_different_users_same_k():
    print("\n2. 不同用户使用相同k (ECDSA)")

    # 用户1签名 - 只需要传递n,G,d,k,e参数
    r31, s31 = ecdsa_sign(n, G, d1, k, e1)

    # 用户2签名
    r32, s32 = ecdsa_sign(n, G, d2, k, e2)

    inv = mul_inv(s31 - s32, n)
    if inv != None:
        k_thr = ((e1 - e2) * inv) % n
        d1_thr = (mul_inv(r31, n) * (k_thr * s31 - e1)) % n  # 恢复d1和d2
        d2_thr = (mul_inv(r32, n) * (k_thr * s32 - e2)) % n
    if (d1_thr == d2_thr):
        print("d1=", d1, "\nd2=", d2)
        print("验证成功\n")
# 3. 与ECDSA共用（d，k）(Schnorr)
def scenario3_shared_dk():
    print("\n3. 与ECDSA共用（d，k）(Schnorr)")
    # ECDSA签名
    r_ecdsa, s_ecdsa = ecdsa_sign(n, G, d1, k, e1)

    # Schnorr签名
    r_schnorr, s_schnorr, e_schnorr = schnorr_sign(m1, n, G, d1, k)

    # 验证签名是否成功
    if r_ecdsa is None or r_schnorr is None:
        print("错误：签名生成失败")
        return

    # 恢复私钥d
    numerator = (s_schnorr * s_ecdsa - e1) % n
    denominator = (r_ecdsa + e_schnorr * s_ecdsa) % n

    if denominator == 0:
        print("错误：分母为0")
        return

    inv_denom = mul_inv(denominator, n)
    if inv_denom is None:
        print("错误：无法计算分母的模逆元")
        return

    d_rec = numerator * inv_denom % n

    print(f"原私钥 d1: {d1}")
    print(f"恢复的私钥 d1: {d_rec}")
    print("验证结果:", "成功" if d_rec == d1 else "失败")


# 4. k值泄漏 (ECDSA)
def scenario4_k_leakage():
    print("\n4. k值泄漏 (ECDSA)")
    r, s = ecdsa_sign(n, G, d1, k, e1)

    # 验证签名是否成功
    if r is None:
        print("错误：签名生成失败")
        return

    # 恢复私钥d
    r_inv = mul_inv(r, n)
    if r_inv is None:
        print("错误：无法计算r的模逆元")
        return

    d_rec = (s * k - e1) * r_inv % n

    print(f"原私钥 d1: {d1}")
    print(f"恢复的私钥 d1: {d_rec}")
    print(f"已知的nonce k: {k}")
    print("验证结果:", "成功" if d_rec == d1 else "失败")


if __name__ == '__main__':
    # 使用小参数进行验证
    a = 5  # 曲线参数a
    b = 7  # 曲线参数b
    p = 11  # 素数域大小（调整为可用的素数）
    G = (5, 1)  # 基点
    n = 11  # 阶数

    k = 2  # 随机数k
    d1 = 3  # 用户1私钥
    d2 = 5  # 用户2私钥

    m1 = 'ljy912'
    m2 = "098765"

    # 生成消息摘要
    e1 = generate(m1, n)  # 消息1摘要
    e2 = generate(m2, n)  # 消息2摘要

    print("基本参数信息:")
    print(f"曲线参数: a={a}, b={b}, p={p}")
    print(f"基点 G: ({G[0]}, {G[1]})")
    print(f"阶数 n: {n}")
    print(f"用户1私钥 d1: {d1}")
    print(f"用户2私钥 d2: {d2}")
    print(f"随机数 k: {k}")
    print(f"消息摘要 e1: {e1} (消息: '{m1}')")
    print(f"消息摘要 e2: {e2} (消息: '{m2}')\n")

    # 测试点乘法以确保曲线工作正常
    test_point = ec_mul(2, G)
    print("曲线测试 (2*G):", test_point)
    if test_point != ec_add(G, G):
        print("警告: 点乘法或点加法可能不正确")

    # 运行四种场景
    scenario1_reuse_k()  # 1) 相同用户重用随机数k
    scenario2_different_users_same_k()  # 2) 不同用户使用相同k
    scenario3_shared_dk()  # 3) 与ECDSA共用（d，k）
    scenario4_k_leakage()  # 4) k值泄漏