import hashlib
import hmac
import random
import binascii

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

    s = (q.y - p.y) * mod_inverse(q.x - p.x, P) % P
    x = (s * s - p.x - q.x) % P
    y = (s * (p.x - x) - p.y) % P
    return ECPoint(x, y)


# 椭圆曲线点加倍
def point_double(p):
    if p.is_infinity():
        return p

    s = (3 * p.x * p.x + A) * mod_inverse(2 * p.y, P) % P
    x = (s * s - 2 * p.x) % P
    y = (s * (p.x - x) - p.y) % P
    return ECPoint(x, y)


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


# KDF 密钥派生函数 (基于 SM3)
def kdf(z, klen):
    ct = 0x00000001
    rcnt = (klen + 31) // 32  # 需要哈希的次数
    out = b''

    for i in range(rcnt):
        ct_bytes = ct.to_bytes(4, 'big')
        data = z + ct_bytes
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
    # 使用 SM3 哈希 (这里用 SHA256 模拟)
    c3 = hashlib.sha256(c3_data).digest()

    # 返回格式: C1(65字节) + C2(明文长度) + C3(32字节)
    c1_bytes = b'\x04' + int_to_bytes(c1.x, 32) + int_to_bytes(c1.y, 32)
    return c1_bytes + ciphertext + c3


# SM2 解密
def sm2_decrypt(priv_key, ciphertext):
    # 解析密文: 前65字节是C1，最后32字节是C3，中间是C2
    if len(ciphertext) < 97:
        raise ValueError("Invalid ciphertext length")

    # 提取C1
    if ciphertext[0] != 0x04:
        raise ValueError("Invalid point format")
    c1x = bytes_to_int(ciphertext[1:33])
    c1y = bytes_to_int(ciphertext[33:65])
    c1 = ECPoint(c1x, c1y)

    # 提取C3和C2
    c3 = ciphertext[-32:]
    cipher_len = len(ciphertext) - 97
    c2 = ciphertext[65:65 + cipher_len]

    # 计算S = [d]C1
    s = point_multiply(priv_key, c1)

    # 计算椭圆曲线点坐标值
    x2 = int_to_bytes(s.x, 32)
    y2 = int_to_bytes(s.y, 32)
    t = kdf(x2 + y2, len(c2))  # 密钥派生

    # 异或解密
    plaintext = bytes(a ^ b for a, b in zip(c2, t))

    # 验证C3
    c3_data = x2 + plaintext + y2
    c3_calc = hashlib.sha256(c3_data).digest()

    if c3 != c3_calc:
        raise ValueError("Ciphertext verification failed")

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
    e = bytes_to_int(hashlib.sha256(e_data).digest())

    # 签名流程
    while True:
        k = random.randrange(1, N)
        p = point_multiply(k, ECPoint(Gx, Gy))
        r = (e + p.x) % N
        if r == 0 or r + k == N:
            continue

        s = mod_inverse(1 + priv_key, N) * (k - r * priv_key) % N
        if s == 0:
            continue

        return (r, s)


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
    e = bytes_to_int(hashlib.sha256(e_data).digest())

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
    return (r % N) == ((e + point.x) % N)


# 测试函数
def test_sm2():
    print("=" * 50)
    print("SM2 Demo")
    print("=" * 50)

    # 密钥生成
    private_key, public_key = generate_keypair()
    print(f"Private Key: {hex(private_key)}")
    print(f"Public Key : {public_key}")

    # 测试数据
    message = b"Hello, SM2 encryption!"
    print(f"\nOriginal Message: {message.decode('utf-8')}")

    # 加密/解密
    ciphertext = sm2_encrypt(public_key, message)
    print(f"\nCiphertext (hex): {binascii.hexlify(ciphertext).decode()}")

    decrypted = sm2_decrypt(private_key, ciphertext)
    print(f"Decrypted Message: {decrypted.decode('utf-8')}")

    # 签名/验证
    signature = sm2_sign(private_key, message)
    print(f"\nSignature (r, s): \nr = {hex(signature[0])}\ns = {hex(signature[1])}")

    is_valid = sm2_verify(public_key, message, signature)
    print(f"Signature Valid: {is_valid}")

    # 篡改测试
    tampered_msg = message + b"tamper"
    is_valid_tampered = sm2_verify(public_key, tampered_msg, signature)
    print(f"Tampered Signature Valid: {is_valid_tampered} (should be False)")


# 运行测试
if __name__ == "__main__":
    test_sm2()