import hashlib
import random
import binascii
import hmac  # 添加缺失的hmac导入

# SM2 推荐曲线参数 (256位素数域)
P = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
A = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
B = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
N = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
Gx = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
Gy = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0


# 椭圆曲线点类
class ECPoint:
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

    def is_infinity(self):
        return self.x is None and self.y is None

    def __str__(self):
        if self.is_infinity():
            return "Point(Infinity)"
        return f"Point({hex(self.x)}, {hex(self.y)})"

    def to_bytes(self, compressed=False):
        if self.is_infinity():
            return b'\x00'  # 无穷远点表示

        if compressed:
            # 压缩格式: 第一位表示y的奇偶性
            prefix = b'\x02' if self.y % 2 == 0 else b'\x03'
            return prefix + self.x.to_bytes(32, 'big')
        else:
            # 未压缩格式
            return b'\x04' + self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')

    @classmethod
    def from_bytes(cls, data):
        if len(data) == 0 or (len(data) == 1 and data[0] == 0x00):  # 无穷远点
            return cls()

        if data[0] == 0x04 and len(data) == 65:  # 未压缩点
            x = int.from_bytes(data[1:33], 'big')
            y = int.from_bytes(data[33:65], 'big')
            return cls(x, y)

        if data[0] in (0x02, 0x03) and len(data) == 33:  # 压缩点
            x = int.from_bytes(data[1:], 'big')
            # 解压缩y坐标 (需要曲线方程)
            y_sq = (x ** 3 + A * x + B) % P
            y = pow(y_sq, (P + 1) // 4, P)  # 模P平方根

            # 根据奇偶性选择正确的y
            if (y % 2 == 0 and data[0] != 0x02) or (y % 2 == 1 and data[0] != 0x03):
                y = P - y
            return cls(x, y)

        raise ValueError(f"Invalid point format: length={len(data)}, first_byte={hex(data[0])}")


# 扩展欧几里得算法求逆元
def mod_inverse(a, m):
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % m, m
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % m


# 椭圆曲线点加法
def point_add(p, q):
    if p.is_infinity():
        return q
    if q.is_infinity():
        return p

    if p.x == q.x and p.y == q.y:
        return point_double(p)

    if p.x == q.x:
        return ECPoint()  # 无穷远点

    slope = (q.y - p.y) * mod_inverse(q.x - p.x, P) % P
    x3 = (slope * slope - p.x - q.x) % P
    y3 = (slope * (p.x - x3) - p.y) % P
    return ECPoint(x3, y3)


# 椭圆曲线点加倍
def point_double(p):
    if p.is_infinity():
        return p

    slope = (3 * p.x * p.x + A) * mod_inverse(2 * p.y, P) % P
    x3 = (slope * slope - 2 * p.x) % P
    y3 = (slope * (p.x - x3) - p.y) % P
    return ECPoint(x3, y3)


# 椭圆曲线点乘 (倍数倍点)
def point_multiply(k, point):
    # 使用二进制展开法
    result = ECPoint()  # 无穷远点
    addend = point

    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_double(addend)
        k >>= 1

    return result


# KDF 密钥派生函数 (基于SM3替代-SHA256)
def kdf(z, klen):
    ct = 0x00000001
    rcnt = (klen + 31) // 32  # 需要哈希的次数
    out = b''

    for i in range(rcnt):
        ct_bytes = ct.to_bytes(4, 'big')
        data = z + ct_bytes
        # 使用SM3哈希替代
        hash_digest = hashlib.sha256(data).digest()
        out += hash_digest
        ct += 1

    return out[:klen]


# 字节转整数 (大端序)
def bytes_to_int(b):
    return int.from_bytes(b, 'big')


# 整数转字节 (大端序，固定长度)
def int_to_bytes(x, size=32):
    return x.to_bytes(size, 'big')


# SM2 密钥对生成
def generate_keypair():
    private_key = random.randrange(1, N)
    public_key = point_multiply(private_key, ECPoint(Gx, Gy))
    return private_key, public_key


# SM2 加密
def sm2_encrypt(pub_key, plaintext):
    k = random.randrange(1, N)
    c1 = point_multiply(k, ECPoint(Gx, Gy))  # C1 = [k]G
    s = point_multiply(k, pub_key)  # [k]P

    # 计算椭圆曲线点坐标值
    x2 = int_to_bytes(s.x, 32)
    y2 = int_to_bytes(s.y, 32)
    t = kdf(x2 + y2, len(plaintext))  # 密钥派生

    # 异或加密
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, t))

    # 计算 C3 (消息摘要)
    c3_data = x2 + plaintext + y2
    # 使用SM3哈希替代
    c3 = hashlib.sha256(c3_data).digest()

    # 返回格式: C1(65字节) + C3(32字节) + C2(明文长度)
    c1_bytes = c1.to_bytes()
    return c1_bytes + c3 + ciphertext


# SM2 解密
def sm2_decrypt(priv_key, ciphertext):
    # 解析密文: 前65字节是C1，接着32字节是C3，后面是C2
    if len(ciphertext) < 97:
        raise ValueError(f"Invalid ciphertext length: {len(ciphertext)} (min 97 required)")

    # 提取C1、C3和C2
    c1 = ECPoint.from_bytes(ciphertext[:65])
    if c1.is_infinity():
        raise ValueError("C1 cannot be infinity point")

    c3 = ciphertext[65:97]
    c2 = ciphertext[97:]

    # 计算S = [d]C1
    s = point_multiply(priv_key, c1)

    # 计算椭圆曲线点坐标值
    x2 = int_to_bytes(s.x, 32)
    y2 = int_to_bytes(s.y, 32)
    t = kdf(x2 + y2, len(c2))  # 密钥派生

    # 异或解密
    plaintext = bytes(a ^ b for a, b in zip(c2, t))

    # 验证C3（使用hmac.compare_digest防止时序攻击）
    c3_data = x2 + plaintext + y2
    c3_calc = hashlib.sha256(c3_data).digest()

    # 使用hmac.compare_digest进行安全比较
    if not hmac.compare_digest(c3, c3_calc):
        raise ValueError("C3 verification failed - possible tampering")

    return plaintext


# SM2 签名
def sm2_sign(priv_key, message, user_id=b"1234567812345678"):
    # 计算 Z_A = HASH256(ENTL || ID || a || b || Gx || Gy || PubX || PubY)
    entl = len(user_id).to_bytes(2, 'big')
    pub_key = point_multiply(priv_key, ECPoint(Gx, Gy))

    data = entl + user_id
    data += int_to_bytes(A, 32) + int_to_bytes(B, 32)
    data += int_to_bytes(Gx, 32) + int_to_bytes(Gy, 32)
    data += int_to_bytes(pub_key.x, 32) + int_to_bytes(pub_key.y, 32)

    za = hashlib.sha256(data).digest()

    # e = HASH(Z_A || message)
    e_data = za + message
    e = bytes_to_int(hashlib.sha256(e_data).digest()) % N

    # 签名流程
    max_attempts = 100
    for attempt in range(max_attempts):
        k = random.randrange(1, N)
        p = point_multiply(k, ECPoint(Gx, Gy))
        r = (e + p.x) % N
        if r == 0:
            continue

        # 检查r + k == N的情况
        if (r + k) % N == 0:
            continue

        inv = mod_inverse(1 + priv_key, N)
        if inv is None:
            continue

        s = inv * (k - r * priv_key) % N
        if s == 0:
            continue

        return (r, s)

    raise RuntimeError(f"Failed to generate signature after {max_attempts} attempts")


# SM2 验签
def sm2_verify(pub_key, message, signature, user_id=b"1234567812345678"):
    r, s = signature

    # 检查范围
    if r < 1 or r >= N or s < 1 or s >= N:
        return False

    # 计算 Z_A
    entl = len(user_id).to_bytes(2, 'big')
    data = entl + user_id
    data += int_to_bytes(A, 32) + int_to_bytes(B, 32)
    data += int_to_bytes(Gx, 32) + int_to_bytes(Gy, 32)
    data += int_to_bytes(pub_key.x, 32) + int_to_bytes(pub_key.y, 32)

    za = hashlib.sha256(data).digest()

    # e = HASH(Z_A || message)
    e_data = za + message
    e = bytes_to_int(hashlib.sha256(e_data).digest()) % N

    # 计算t = (r + s) mod N
    t = (r + s) % N
    if t == 0:
        return False

    # 计算椭圆曲线点 (s)G + (t)PubKey
    p1 = point_multiply(s, ECPoint(Gx, Gy))
    p2 = point_multiply(t, pub_key)
    point = point_add(p1, p2)

    if point.is_infinity():
        return False

    # 验证 R = (e + x) mod N
    r_calculated = (e + point.x) % N
    return r_calculated == r


# 测试函数
def test_sm2():
    print("=" * 50)
    print("SM2 Elliptic Curve Cryptography Demo")
    print("=" * 50)

    # 密钥生成
    private_key, public_key = generate_keypair()
    print(f"Private Key: {hex(private_key)}")
    print(f"Public Key: {public_key}")
    print(f"Compressed Public Key: {public_key.to_bytes(compressed=True).hex()}")

    # 测试数据
    message = b"Hello, SM2 encryption! This is a test message."
    print(f"\nOriginal Message: {message.decode('utf-8')}")
    print(f"Message length: {len(message)} bytes")

    # 加密/解密
    ciphertext = sm2_encrypt(public_key, message)
    print(f"\nCiphertext length: {len(ciphertext)} bytes")
    print(f"First 32 chars of ciphertext (hex): {binascii.hexlify(ciphertext[:32]).decode()}")

    decrypted = sm2_decrypt(private_key, ciphertext)
    print(f"\nDecrypted Message: {decrypted.decode('utf-8')}")

    # 签名/验证
    signature = sm2_sign(private_key, message)
    print(f"\nSignature (r, s): \nr = {hex(signature[0])}\ns = {hex(signature[1])}")

    is_valid = sm2_verify(public_key, message, signature)
    print(f"Signature Valid: {is_valid}")

    # 篡改测试
    tampered_msg = message + b"tamper"
    is_valid_tampered = sm2_verify(public_key, tampered_msg, signature)
    print(f"Tampered Signature Valid: {is_valid_tampered} (should be False)")

    # 自加密测试
    print("\nTesting encryption/decryption roundtrip...")
    test_messages = [
        b"",
        b"Short",
        b"Medium length message",
        b"A" * 100,
        b"B" * 1000
    ]

    for msg in test_messages:
        ct = sm2_encrypt(public_key, msg)
        pt = sm2_decrypt(private_key, ct)
        assert pt == msg, f"Roundtrip failed for message: {msg}"
        print(f"✓ Length {len(msg):4} bytes: passed")

    print("\nAll tests passed successfully!")


# 运行测试
if __name__ == "__main__":
    try:
        test_sm2()
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback

        traceback.print_exc()