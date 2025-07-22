from gmssl import sm3, func
import random
import string
import math
import time


def create(record_list):
    table = []
    lst = []
    for i in record_list:
        temp = sm3.sm3_hash(func.bytes_to_list(i.encode()))
        lst.append(temp)
    table.append(lst[:])
    if len(lst) <= 1:
        print("no tracnsactions to be hashed")
        return False
    height = 1  # 高度
    while len(lst) > 1:
        height += 1
        if len(lst) % 2 == 0:
            lstt = []
            while len(lst) > 1:
                a = lst.pop(0)
                b = lst.pop(0)
                temp = sm3.sm3_hash(func.bytes_to_list((a + b).encode()))
                lstt.append(temp)
            lst = lstt
        else:  # 奇数个点，复制最后一个，凑偶数个
            lstt = []
            lst.append(lst[-1])
            while len(lst) > 1:
                a = lst.pop(0)
                b = lst.pop(0)  
                temp = sm3.sm3_hash(func.bytes_to_list((a + b).encode()))
                lstt.append(temp)
            lst = lstt
        table.append(lst[:])
    return lst, height, table


record_list = [ 'jing', 'dd', 'dddd', 'w', 'aa', 'n', 'ddd', 'e', 'ee', 'qq', 'wfag', 'aaa', 'bb']
listt, height, table = create(record_list)
print("proof:", listt)
#print("所有层级哈希值:",table)
print("height:", height)

'''
#十万叶子节点,计时
def random_string_generate(size,allowed_chars):
    return ''.join(random.choice(allowed_chars)for x in range(size))

allowed_chars=string.ascii_letters+string.punctuation

record_list=[]
num=100000
for i in range(num):
    record_list.append(random_string_generate(5,allowed_chars))
print("ok")
t_start=time.time()
listt,height,table=create(record_list)
t_end=time.time()
print("height:",height)
print("创建{}叶子节点的merkle tree所需时间为{}s".format(num,t_end-t_start))


'''
# 节点包含证明
def include_proof(tx, pos, height, table):
    lls = []
    for i in range(height):
        lls += [pos]
        pos = pos // 2
    # 相邻位置列表
    ls = []
    for i in lls[:-1]:
        if i % 2 == 0:
            ls.append(i + 1)
        else:
            ls.append(i - 1)
    ls.append(0)  # 添加proof
    T_list = []
    for i in range(height):
        if (ls[i] >= len(table[i])):  ##若越界，则是填充重复的
            T_list.append(table[i][-1])
        else:
            T_list.append(table[i][ls[i]])
    a = tx
    # a=sm3.sm3_hash(func.bytes_to_list(tx.encode()))
    for i in range(height - 1):
        b = T_list[i]
        if lls[i] % 2 == 0:
            a = sm3.sm3_hash(func.bytes_to_list((a + b).encode()))
        else:
            a = sm3.sm3_hash(func.bytes_to_list((b + a).encode()))
    if a != T_list[-1]:
        return False
    return True

'''
tx = ('aa')
print(tx)
pos = record_list.index(tx)
tx = sm3.sm3_hash(func.bytes_to_list(tx.encode()))
print(tx, pos)
if_exist = include_proof(tx, pos, height, table)
if if_exist == True:
    print("该节点存在")
else:
    print("该节点不存在")'''

def exclude_proof(pos1,pos2,table):
    try:

        temp=sm3.sm3_hash(func.bytes_to_list((table[0][pos1]+table[0][pos2]).encode()))
        try:
            pos=table[1].index(temp)
            if_exist=include_proof(temp,pos,height-1,table[1:])
            return if_exist
        except:

            for i in range(height-1):
                a=table[i][pos1-1]
                b=table[i][pos1]
                c=table[i][pos2]
                d=table[i][pos2+1]
                h1=sm3.sm3_hash(func.bytes_to_list((a+b).encode()))
                h2=sm3.sm3_hash(func.bytes_to_list((c+d).encode()))
                #print(h1,h2)

                temp=sm3.sm3_hash(func.bytes_to_list((h1+h2).encode()))
                #print(temp)
                for j in range(len(table[i+1])):
                    if_exist=include_proof(temp,j,height-2-i,table[2+i:])
                    if if_exist==True:
                        return True
                #不相连的话，再次尝试下一轮
                pos1=table[i+1].index(h1)
                pos2=table[i+1].index(h2)
    except:
        return False






pos1=2
pos2=4
print(pos1,pos2)
if_note=exclude_proof(pos1,pos2,table)
if if_note==True:
    print("两端节点相邻，该节点不存在")
else:
    print("该节点存在")
