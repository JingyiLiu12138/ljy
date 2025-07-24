import random
import hashlib
from ecdsa import NIST256p
from ecdsa.ellipticcurve import PointJacobi
from phe import paillier  # 加法同态加密库

# 初始化椭圆曲线
curve = NIST256p.curve
G = NIST256p.generator
n = NIST256p.order  # 曲线阶数


# 点序列化（65字节未压缩格式）
def serialize_point(point):
    return point.to_bytes(encoding='uncompressed')


# 点反序列化
def deserialize_point(data):
    return PointJacobi.from_bytes(curve, data)


# 哈希函数（字符串 -> 曲线点）
def hash_to_point(input_str):
    h = hashlib.sha256(input_str.encode()).digest()
    h_int = int.from_bytes(h, 'big') % n
    if h_int == 0:
        h_int = 1  # 避免0
    return h_int * G


# 洗牌函数
def shuffle_list(input_list):
    shuffled = input_list[:]
    random.shuffle(shuffled)
    return shuffled


class DDHPrivateIntersectionSum:
    def __init__(self, p1_data, p2_data):
        self.p1_data = p1_data  # P1的集合 [str]
        self.p2_data = p2_data  # P2的集合 [(str, int)]

        # 生成密钥
        self.k1 = random.randint(1, n - 1)  # P1私钥
        self.k2 = random.randint(1, n - 1)  # P2私钥
        self.paillier_pub, self.paillier_priv = paillier.generate_paillier_keypair(n_length=768)  # Paillier密钥

    def round1_p1(self):
        """P1: 计算H(v_i)^k1并发送"""
        self.p1_processed = []
        for v in self.p1_data:
            point = hash_to_point(v)
            exp_point = self.k1 * point  # g^{k1}
            self.p1_processed.append(exp_point)
        return shuffle_list(self.p1_processed)

    def round2_p2(self, p1_points):
        # 1. 双加密P1的点
        dual_enc_points = [self.k2 * p for p in p1_points]

        # 2. 准备P2的数据（保持点和值的对应关系）
        self.p2_enc_points = []
        self.p2_enc_values = []
        for w, t_val in self.p2_data:
            point = hash_to_point(w)
            exp_point = self.k2 * point
            enc_t = self.paillier_pub.encrypt(t_val)
            self.p2_enc_points.append(exp_point)
            self.p2_enc_values.append(enc_t)

        # 3. 一起洗牌点和值（保持对应关系）
        combined = list(zip(self.p2_enc_points, self.p2_enc_values))
        random.shuffle(combined)
        self.p2_enc_points, self.p2_enc_values = zip(*combined)

        return shuffle_list(dual_enc_points), list(self.p2_enc_points), list(self.p2_enc_values)

    def round3_p1(self, dual_enc_points, p2_points, p2_enc_values):
        """P1: 计算交集和同态和"""
        # 计算交集
        valid_indices = []
        for i, p2_point in enumerate(p2_points):
            dual_p2_point = self.k1 * p2_point  # 双加密点
            if dual_p2_point in dual_enc_points:
                valid_indices.append(i)

        # 同态求和（交集内的值）
        sum_ciphertext = self.paillier_pub.encrypt(0)
        for idx in valid_indices:
            sum_ciphertext += p2_enc_values[idx]

        self.intersection_size = len(valid_indices)
        return sum_ciphertext

    def final_output_p2(self, sum_ciphertext):
        """P2: 解密获得总和"""
        intersection_sum = self.paillier_priv.decrypt(sum_ciphertext)
        return self.intersection_size, intersection_sum


# 测试示例
if __name__ == "__main__":
    # 测试数据（实际应用中更大）
    p1_set = ["id1", "id2", "id3", "id5"]
    p2_set = [("id2", 10), ("id3", 20), ("id4", 30), ("id5", 40)]

    protocol = DDHPrivateIntersectionSum(p1_set, p2_set)

    # Round 1: P1发送数据
    p1_to_p2 = protocol.round1_p1()

    # Round 2: P2发送两组数据
    dual_points, p2_points, p2_enc_values = protocol.round2_p2(p1_to_p2)

    # Round 3: P1计算并返回加密和
    sum_ciphertext = protocol.round3_p1(dual_points, p2_points, p2_enc_values)

    # P2解密结果
    intersection_size, intersection_sum = protocol.final_output_p2(sum_ciphertext)

    print(f"交集大小: {intersection_size}")  # 应输出3 (id2,id3,id5)
    print(f"交集值总和: {intersection_sum}")  # 应输出70 (10+20+40)