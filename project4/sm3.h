
#include <iostream>
#include <intrin.h>
using namespace std;

#define u8 unsigned char
#define u32 unsigned long

void SM3(u8* input, unsigned int len, u8* output);
void printt_u8(u8* input);
void u8_32(u8* in, u32* out);
u32 shift_l(u32 a, u8 w);

__m128i indexx = _mm_setr_epi8(3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12);

/*u32 IV[8] = {
	0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
	0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e
};*/

u32 T[2] = {
	0x79cc4519,0x7a879d8a
};
u32 FF0(u32 x, u32 y, u32 z) {
	return x ^ y ^ z;
}
u32 FF1(u32 x, u32 y, u32 z) {
	return((x & y) | (x & z) | (y & z));
}
u32 GG0(u32 x, u32 y, u32 z) {
	return x ^ y ^ z;
}
u32 GG1(u32 x, u32 y, u32 z) {
	return (x & y) | (~x & z);
}

u32 shift_l(u32 a, u8 w) {
	w = w % 32;
	if (w == 0) {
		return a;
	}
	return (a << w) ^ (a >> (32 - w));
}
void u8_32(u8* in, u32* out) {
	/*
	//原始版本
	for (u8 i = 0; i < 4; i++) {
		u32 temp = 0;
		for (u8 j = 0; j < 4; j++) {
			temp = temp ^ ((u32)in[4 * i + j] << (24 - 8 * j));
		}
		out[i] = temp;
	}
	*/
	/*
	//循环展开后
	for (u8 i = 0; i < 4; i++) {
		int ii = i << 2;
		u32 temp = ((u32)in[ii] << 24);//循环稍微展开一下
		temp = temp ^ ((u32)in[ii + 1] << 16);
		temp = temp ^ ((u32)in[ii + 2] << 8);
		temp = temp ^ (u32)in[ii + 3];
		out[i] = temp;
	}*/
	//SIMD版本
	__m128i tp = _mm_loadu_epi8(&in[0]);
	tp = _mm_shuffle_epi8(tp, indexx);//指定个顺序避免大端小端
	_mm_storeu_epi32(&out[0], tp);
}


u32 V[8];
u8 iin[64] = { 0 };

void message_block(u8* input);

void SM3(u8* input, unsigned int len, u8* output)
{
	//512比特（64字节）分组，消息填充
	//第一次的iv为初始值，固定不引用了。
	V[0] = 0x7380166f;
	V[1] = 0x4914b2b9;
	V[2] = 0x172442d7;
	V[3] = 0xda8a0600;
	V[4] = 0xa96f30bc;
	V[5] = 0x163138aa;
	V[6] = 0xe38dee4d;
	V[7] = 0xb0fb0e4e;
	int temp_i = len >> 6;
	for (unsigned int i = 0; i < temp_i; i++) {
		message_block(input + (i << 6));
	}
	//最后一组填充
	int temp1 = (len >> 6) << 6;
	int temp2 = len % 64;
	for (int i = 0; i < temp2; i++) {
		iin[i] = input[temp1 + i];
	}
	iin[temp2] = 0x80;
	unsigned int llen = len << 3;
	iin[60] = llen >> 24;
	iin[61] = llen >> 16;
	iin[62] = llen >> 8;
	iin[63] = llen;
	//这里的长度默认小于32，故56，57，58，59默认为0
	message_block(iin);

	//返回output；
	for (int i = 0; i < 8; i++) {
		int ii = i << 2;
		output[ii] = V[i] >> 24;
		output[ii + 1] = V[i] >> 16;
		output[ii + 2] = V[i] >> 8;
		output[ii + 3] = V[i];
	}
}
void message_block(u8* iinput)//每个消息分组处理
{
	//消息扩展
	u32 W[68];
	u32 W_[64];
	for (int i = 0; i < 16; i++) {
		u8_32(iinput + (i << 2), &W[i]);
	}
	u32 temp;
	for (int i = 16; i < 68; i++) {
		//P1(X) = X ⊕ (X ? 15) ⊕ (X ? 23)
		//Wj ← P1(Wj?16 ⊕ Wj?9 ⊕ (Wj?3 ? 15)) ⊕ (Wj?13 ? 7) ⊕ Wj?6
		temp = W[i - 16] ^ W[i - 9] ^ (shift_l(W[i - 3], 15));
		temp = temp ^ (shift_l(temp, 15)) ^ (shift_l(temp, 23));
		W[i] = temp ^ (shift_l(W[i - 13], 7)) ^ W[i - 6];
	}
	for (int i = 0; i < 64; i += 2) {
		//W′j = Wj ⊕ Wj + 4
		//循环展开
		W_[i] = W[i] ^ W[i + 4];
		W_[i + 1] = W[i + 1] ^ W[i + 5];
	}

	//迭代压缩
	//迭代每一轮相关，无法多线程并行
	u32 A = V[0];
	u32 B = V[1];
	u32 C = V[2];
	u32 D = V[3];
	u32 E = V[4];
	u32 F = V[5];
	u32 G = V[6];
	u32 H = V[7];
	u32 SS1, SS2, TT1, TT2;
	for (int i = 0; i < 16; i++) {
		SS1 = (shift_l(A, 12)) + E + (shift_l(T[0], i));
		SS1 = shift_l(SS1, 7);
		SS2 = SS1 ^ (shift_l(A, 12));
		TT1 = FF0(A, B, C) + D + SS2 + W_[i];
		TT2 = GG0(E, F, G) + H + SS1 + W[i];
		D = C;
		C = shift_l(B, 9);
		B = A;
		A = TT1;
		H = G;
		G = shift_l(F, 19);
		F = E;
		E = TT2 ^ (shift_l(TT2, 9)) ^ (shift_l(TT2, 17));
	}
	for (int i = 16; i < 64; i++) {
		SS1 = (shift_l(A, 12)) + E + (shift_l(T[1], i));
		SS1 = shift_l(SS1, 7);
		SS2 = SS1 ^ (shift_l(A, 12));
		TT1 = FF1(A, B, C) + D + SS2 + W_[i];
		TT2 = GG1(E, F, G) + H + SS1 + W[i];
		D = C;
		C = shift_l(B, 9);
		B = A;
		A = TT1;
		H = G;
		G = shift_l(F, 19);
		F = E;
		E = TT2 ^ (shift_l(TT2, 9)) ^ (shift_l(TT2, 17));
	}
	V[0] = A ^ V[0];
	V[1] = B ^ V[1];
	V[2] = C ^ V[2];
	V[3] = D ^ V[3];
	V[4] = E ^ V[4];
	V[5] = F ^ V[5];
	V[6] = G ^ V[6];
	V[7] = H ^ V[7];
}
