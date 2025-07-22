#pragma once
#pragma once


#include<stdint.h>
#include<stdlib.h>
#include<string.h>
#include<vector>
using namespace std;

#define SM3_A 0x7380166f
#define SM3_B 0x4914b2b9
#define SM3_C 0x172442d7
#define SM3_D 0xda8a0600
#define SM3_E 0xa96f30bc
#define SM3_F 0x163138aa
#define SM3_G 0xe38dee4d
#define SM3_H 0xb0fb0e4e

//长度拓展攻击使用的已知压缩值H(M0)
#define extend_attack_A 0x66c7f0f4
#define extend_attack_B 0x62eeedd9
#define extend_attack_C 0xd1f2d46b
#define extend_attack_D 0xdc10e4e2
#define extend_attack_E 0x4167c487
#define extend_attack_F 0x5cf2f7a2
#define extend_attack_G 0x297da02b
#define extend_attack_H 0x8f4ba8e0


#define T0 0x79cc4519
#define T1 0x7a879d8a



#define shift_left(n,step)		((n<<step)|(n>>(32-step)))
#define P0(X) (X^(shift_left(X,9))^(shift_left(X,17)))
#define P1(X) (X^(shift_left(X,15))^(shift_left(X,23)))
#define FF0(X,Y,Z) (X^Y^Z)
#define FF1(X,Y,Z) ((X&Y)|(X|Y)&Z)
#define GG0(X,Y,Z) ((X)^(Y)^(Z))
#define GG1(X,Y,Z) ((X&Y)|((~X)&Z))


uint32_t Padding(vector<bool>* input, uint32_t* M);								//消息填充
uint32_t Padding_extend_attack(vector<bool>* input, uint32_t* M, uint64_t len);
void Extend(uint32_t* M, uint32_t* W0, uint32_t* W1);								//消息拓展
void Compress(uint32_t* V, uint32_t* W0, uint32_t* W1, uint32_t* res);						//压缩函数
void SM3(vector<bool>* input, uint32_t* digest);
void SM3_extend_attack(vector<bool>* input, uint32_t* digest, uint64_t len);					//长度扩展攻击


uint32_t Padding(vector<bool>* input, uint32_t* M)
{
	uint64_t size = (*input).size(), len = size;
	uint32_t pad_size = (447 - size + 512) % 512, temp;
	size = size + 1 + (uint64_t)pad_size;
	(*input).push_back(1);											//末尾添1
	(*input).resize(size, 0);
	for (uint32_t i = 0; i < size; i += 32)
	{
		temp = 0;
		for (uint32_t j = 0; j < 31; ++j)
		{
			temp |= (*input)[i + j]; temp <<= 1;
		}
		temp |= (*input)[i + 31];
		M[(uint32_t)(i / 32)] = temp;
	}
	M[(uint32_t)(size / 32)] = (uint32_t)(len >> 32);
	M[(uint32_t)(size / 32 + 1)] = ((uint32_t)len);
	return (uint32_t)((size / 32 + 2) / 16);								//返回分组数
}

uint32_t Padding_extend_attack(vector<bool>* input, uint32_t* M, uint64_t len)
{
	uint64_t size = (*input).size();
	uint32_t pad_size = (447 - size + 512) % 512, temp;
	size = size + 1 + (uint64_t)pad_size;
	(*input).push_back(1);											//末尾添1
	(*input).resize(size, 0);
	for (uint32_t i = 0; i < size; i += 32)
	{
		temp = 0;
		for (uint32_t j = 0; j < 31; ++j)
		{
			temp |= (*input)[i + j]; temp <<= 1;
		}
		temp |= (*input)[i + 31];
		M[(uint32_t)(i / 32)] = temp;
	}
	M[(uint32_t)(size / 32)] = (uint32_t)(len >> 32);							//长度拓展攻击已知前面明文的长度
	M[(uint32_t)(size / 32 + 1)] = ((uint32_t)len);
	return (uint32_t)((size / 32 + 2) / 16);
}

void Extend(uint32_t* M, uint32_t* W0, uint32_t* W1)								//W0和W0'消息拓展
{
	for (uint32_t i = 0; i < 16; i++)
		W0[i] = M[i];

	for (uint32_t i = 16; i < 68; ++i)
		W0[i] = (P1((W0[i - 16] ^ W0[i - 9] ^ (shift_left(W0[i - 3], 15))))) ^ (shift_left(W0[i - 13], 7)) ^ W0[i - 6];

	for (uint32_t i = 0; i < 64; ++i)
		W1[i] = W0[i] ^ W0[i + 4];
}

void Compress(uint32_t* V, uint32_t* W0, uint32_t* W1, uint32_t* res)	//单分组压缩函数
{
	uint32_t  A, B, C, D, E, F, G, H, SS1, SS2, TT1, TT2;
	A = V[0]; B = V[1]; C = V[2]; D = V[3]; E = V[4]; F = V[5]; G = V[6]; H = V[7];
	for (uint32_t i = 0; i < 16; ++i)
	{
		SS1 = (uint32_t)shift_left((shift_left(A, 12) + E + shift_left(T0, i)), 7);
		SS2 = SS1 ^ shift_left(A, 12);
		TT1 = (uint32_t)(FF0(A, B, C) + D + SS2 + W1[i]);
		TT2 = (uint32_t)(GG0(E, F, G) + H + SS1 + W0[i]);
		D = C; C = shift_left(B, 9); B = A;
		A = TT1; H = G; G = shift_left(F, 19);
		F = E; E = P0(TT2);
	}
	for (uint32_t i = 16; i < 64; ++i)
	{
		SS1 = (uint32_t)shift_left((shift_left(A, 12) + E + shift_left(T1, i % 32)), 7);
		SS2 = SS1 ^ shift_left(A, 12);
		TT1 = (uint32_t)(FF1(A, B, C) + D + SS2 + W1[i]);
		TT2 = (uint32_t)(GG1(E, F, G) + H + SS1 + W0[i]);
		D = C; C = shift_left(B, 9); B = A;
		A = TT1; H = G; G = shift_left(F, 19);
		F = E; E = P0(TT2);
	}
	res[0] = A ^ V[0]; res[1] = B ^ V[1];
	res[2] = C ^ V[2]; res[3] = D ^ V[3];
	res[4] = E ^ V[4]; res[5] = F ^ V[5];
	res[6] = G ^ V[6]; res[7] = H ^ V[7];
}

void SM3(vector<bool>* input, uint32_t* digest)
{
	uint32_t W0[68], W1[64], V[8], M[80], len;		//这里假设填充后最大长度为5个512bit分组
	len = Padding(input, M);
	V[0] = SM3_A; V[1] = SM3_B; V[2] = SM3_C; V[3] = SM3_D; V[4] = SM3_E; V[5] = SM3_F; V[6] = SM3_G; V[7] = SM3_H;
	for (uint32_t i = 0; i < len; i++)				//对所有分组执行压缩函数
	{
		Extend(M + (i << 4), W0, W1);
		Compress(V, W0, W1, digest);
		for (uint32_t j = 0; j < 8; j++)			//前一次输出的V为下一次输入
			V[j] = digest[j];
	}
}

void SM3_extend_attack(vector<bool>* input, uint32_t* digest, uint64_t length)
{
	uint32_t W0[68], W1[64], V[8], M[80], len;
	len = Padding_extend_attack(input, M, length);
	V[0] = extend_attack_A; V[1] = extend_attack_B; V[2] = extend_attack_C; V[3] = extend_attack_D;		//将起始的V替换成已有的上一轮压缩结果
	V[4] = extend_attack_E; V[5] = extend_attack_F; V[6] = extend_attack_G; V[7] = extend_attack_H;
	for (uint32_t i = 0; i < len; i++)
	{
		Extend(M + (i << 4), W0, W1);
		Compress(V, W0, W1, digest);
		for (uint32_t j = 0; j < 8; j++)
			V[j] = digest[j];
	}
}