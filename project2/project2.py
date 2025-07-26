import numpy as np
import cv2
import pywt
import matplotlib.pyplot as plt
from skimage.util import random_noise
import os


# ======================
# 核心功能实现
# ======================

def generate_watermark(shape, text=None):
    """生成二值水印图像"""
    if text:
        # 文字水印
        img = np.zeros(shape, dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (10, shape[0] // 2), font, 1, 255, 2)
        return img
    else:
        # 随机图案水印
        return np.random.choice([0, 255], size=shape, p=[0.5, 0.5]).astype(np.uint8)


def embed_watermark(cover, watermark, alpha=0.1, level=2):
    """在封面图像中嵌入水印"""
    # 调整水印大小
    watermark = cv2.resize(watermark, (cover.shape[1] // (2 ** level), cover.shape[0] // (2 ** level)))

    # 转换为float类型
    cover = cover.astype(np.float32)
    watermark = watermark.astype(np.float32) / 255

    # 多级小波分解
    coeffs = pywt.wavedec2(cover, 'haar', level=level)

    # 在HL子带嵌入水印
    hl = coeffs[1][1]
    hl_wm = hl + alpha * watermark * np.max(hl)

    # 更新系数
    coeffs_wm = [coeffs[0]] + list(coeffs[1:])
    coeffs_wm[1] = (coeffs_wm[1][0], hl_wm, coeffs_wm[1][2])

    # 小波重构
    watermarked = pywt.waverec2(coeffs_wm, 'haar')

    # 归一化处理
    watermarked = np.clip(watermarked, 0, 255).astype(np.uint8)

    return watermarked, watermark


def extract_watermark(watermarked, original, watermark_shape, alpha=0.1, level=2):
    """从图像中提取水印"""
    # 多级小波分解
    coeffs_wm = pywt.wavedec2(watermarked.astype(np.float32), 'haar', level=level)
    coeffs_orig = pywt.wavedec2(original.astype(np.float32), 'haar', level=level)

    # 提取HL子带差异
    hl_wm = coeffs_wm[1][1]
    hl_orig = coeffs_orig[1][1]
    watermark_extracted = (hl_wm - hl_orig) / alpha / np.max(hl_orig)

    # 缩放、二值化和裁剪
    watermark_extracted = np.clip(watermark_extracted, 0, 1)
    watermark_extracted = (watermark_extracted * 255).astype(np.uint8)
    watermark_extracted = cv2.resize(watermark_extracted, watermark_shape[::-1])

    # 二值化处理
    _, extracted = cv2.threshold(watermark_extracted, 128, 255, cv2.THRESH_BINARY)

    return extracted


def calculate_ber(original_wm, extracted_wm):
    """计算误码率(Bit Error Rate)"""
    if original_wm.shape != extracted_wm.shape:
        extracted_wm = cv2.resize(extracted_wm, original_wm.shape[::-1])
    return np.mean(original_wm != extracted_wm)


# ======================
# 攻击测试函数
# ======================

def apply_attacks(img, attack_type='gaussian_noise', severity=1):
    """应用各种攻击"""
    attacked = img.copy()

    if attack_type == 'rotation':
        angle = 20 * severity
        M = cv2.getRotationMatrix2D((img.shape[1] // 2, img.shape[0] // 2), angle, 1)
        attacked = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))

    elif attack_type == 'scaling':
        scale = 1 - 0.1 * severity
        attacked = cv2.resize(img, None, fx=scale, fy=scale)
        attacked = cv2.resize(attacked, (img.shape[1], img.shape[0]))

    elif attack_type == 'cropping':
        h, w = img.shape[:2]
        crop_percent = 0.1 * severity
        cropped = img[int(h * crop_percent):int(h * (1 - crop_percent)),
                  int(w * crop_percent):int(w * (1 - crop_percent))]
        attacked = cv2.resize(cropped, (w, h))

    elif attack_type == 'gaussian_noise':
        mean = 0
        var = 0.005 * severity
        attacked = random_noise(img, mode='gaussian', mean=mean, var=var)
        attacked = (attacked * 255).astype(np.uint8)

    elif attack_type == 'contrast_change':
        contrast = 1 + 0.3 * severity
        attacked = np.clip(img.astype(np.float32) * contrast, 0, 255).astype(np.uint8)

    elif attack_type == 'blurring':
        kernel_size = 2 * severity + 1
        attacked = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

    return attacked


# ======================
# 测试与可视化
# ======================

def main():
    # 创建目录保存结果
    os.makedirs('results', exist_ok=True)

    # 1. 生成原图和水印
    if not os.path.exists('lena.jpg'):
        print("正在下载Lena图像...")
        import urllib.request
        url = 'https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png'
        urllib.request.urlretrieve(url, 'lena.jpg')

    cover = cv2.imread('lena.jpg', cv2.IMREAD_GRAYSCALE)
    if cover is None:
        # 如果下载的lena.jpg不可用，则创建一张测试图像
        print("创建测试图像...")
        cover = np.zeros((512, 512), dtype=np.uint8)
        cv2.putText(cover, "Test Image", (150, 256), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)

    watermark = generate_watermark((100, 200), text='SECRET')

    cv2.imwrite('results/01_cover.jpg', cover)
    cv2.imwrite('results/02_watermark.png', watermark)

    # 2. 嵌入水印
    watermarked, scaled_wm = embed_watermark(cover, watermark)
    cv2.imwrite('results/03_watermarked.jpg', watermarked)

    # 3. 原始提取
    extracted = extract_watermark(watermarked, cover, watermark.shape)
    cv2.imwrite('results/04_extracted.png', extracted)
    ber = calculate_ber(watermark, extracted)
    print(f"原始提取BER: {ber:.4f}")

    # 4. 鲁棒性测试
    attacks = ['rotation', 'scaling', 'cropping', 'gaussian_noise', 'contrast_change', 'blurring']
    results = []

    # 创建更大的图像展示区域 (4x3 网格)
    fig, axs = plt.subplots(4, 3, figsize=(15, 16))

    # 第一行显示原始信息
    axs[0, 0].imshow(cover, cmap='gray')
    axs[0, 0].set_title('原始图像')
    axs[0, 0].axis('off')

    axs[0, 1].imshow(watermarked, cmap='gray')
    axs[0, 1].set_title('含水印图像 (PSNR: {:.2f}dB)'.format(
        10 * np.log10(255 ** 2 / np.mean((cover.astype(float) - watermarked.astype(float)) ** 2))))
    axs[0, 1].axis('off')

    axs[0, 2].imshow(extracted, cmap='gray')
    axs[0, 2].set_title(f'提取水印\nBER={ber:.4f}')
    axs[0, 2].axis('off')

    # 后三行显示攻击效果
    for i, attack in enumerate(attacks):
        attacked = apply_attacks(watermarked, attack, severity=2)
        extracted_attacked = extract_watermark(attacked, cover, watermark.shape)
        ber = calculate_ber(watermark, extracted_attacked)
        results.append((attack, ber))

        # 计算行和列索引 (每行3个)
        row = i // 3 + 1
        col = i % 3

        # 显示攻击后的图像
        axs[row, col].imshow(attacked, cmap='gray')
        axs[row, col].set_title(f'{attack}攻击后的图像')
        axs[row, col].axis('off')

        # 显示攻击后提取的水印
        axs[row + 1, col].imshow(extracted_attacked, cmap='gray')
        axs[row + 1, col].set_title(f'提取水印\nBER={ber:.4f}')
        axs[row + 1, col].axis('off')

        cv2.imwrite(f'results/05_{attack}_attacked.jpg', attacked)
        cv2.imwrite(f'results/06_{attack}_extracted.png', extracted_attacked)

    # 添加攻击类型标签
    for i in range(3):
        axs[1, i].text(0.5, -0.15, attacks[i], transform=axs[1, i].transAxes,
                       ha='center', fontsize=12)
        axs[3, i].text(0.5, -0.15, attacks[i + 3], transform=axs[3, i].transAxes,
                       ha='center', fontsize=12)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3, wspace=0.1)
    plt.savefig('results/07_robustness_test.png')
    plt.close()

    # 打印结果
    print("\n鲁棒性测试结果:")
    for attack, ber in results:
        print(f"{attack:15s} -> BER: {ber:.4f}")


if __name__ == "__main__":
    main()