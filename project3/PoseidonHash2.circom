pragma circom 2.1.6;

include "./circomlib/circuits/poseidon.circom";

template PoseidonHash2() {
    signal input in[2];  // 隐私输入（原象）
    signal output out;   // 公开输出（哈希值）

    component p = Poseidon(2);  // t=3（2输入 + 1 padding）
    for (var i = 0; i < 2; i++) {
        p.inputs[i] <== in[i];
    }
    out <== p.out;
}

component main = PoseidonHash2();

/* INPUT ={
  "in": ["123", "456"]
}*/
