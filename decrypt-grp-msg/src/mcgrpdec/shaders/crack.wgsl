// MeshCore #hashtag-room name brute-forcer — Vulkan compute (WGSL).
//
// Each invocation tests one candidate name:
//   key   = SHA256(namebytes)[:16]
//   chash = SHA256(key)[0]                         -> must equal TARGET_CHASH
//   mac   = HMAC-SHA256(key||0^16, CIPHERTEXT)[:2] -> must equal TARGET_MAC
// A candidate is written to the output buffer only if BOTH match, so the host
// gets essentially only true hits (24-bit tag) and confirms by decrypting.
//
// Per-packet constants are substituted by gpu.py before compilation
// (/*...*/ sentinels). CIPHERTEXT is baked as the inner HMAC block1.

struct Params {
    base: u32,          // charset length
    name_len: u32,      // L (chars, excluding any '#')
    inner_len: u32,     // chars enumerated by gid (low-order positions)
    inner_count: u32,   // base^inner_len
    stride_x: u32,      // threads per row for 2D dispatch linearization
    use_hash: u32,      // 1 => hash "#"+name, 0 => hash name
    high_len: u32,      // name_len - inner_len (fixed high chars)
    _pad: u32,
    target_chash: u32,
    target_mac0: u32,
    target_mac1: u32,
    _pad2: u32,
};

@group(0) @binding(0) var<uniform> P: Params;
@group(0) @binding(1) var<storage, read> charset: array<u32>;    // one byte per element
@group(0) @binding(2) var<storage, read> high_bytes: array<u32>; // fixed high chars, name order
@group(0) @binding(3) var<storage, read_write> out_count: atomic<u32>;
@group(0) @binding(4) var<storage, read_write> out_gids: array<u32>;

const K = array<u32, 64>(
    0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
    0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
    0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
    0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
    0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
    0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
    0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
    0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u,
);

fn rotr(x: u32, n: u32) -> u32 { return (x >> n) | (x << (32u - n)); }

// Compress one 512-bit block (w[0..15]) into state h[0..7].
fn compress(h: ptr<function, array<u32,8>>, blk: ptr<function, array<u32,16>>) {
    var w: array<u32, 64>;
    for (var i = 0u; i < 16u; i = i + 1u) { w[i] = (*blk)[i]; }
    for (var i = 16u; i < 64u; i = i + 1u) {
        let s0 = rotr(w[i-15u],7u) ^ rotr(w[i-15u],18u) ^ (w[i-15u] >> 3u);
        let s1 = rotr(w[i-2u],17u) ^ rotr(w[i-2u],19u) ^ (w[i-2u] >> 10u);
        w[i] = w[i-16u] + s0 + w[i-7u] + s1;
    }
    var a=(*h)[0]; var b=(*h)[1]; var c=(*h)[2]; var d=(*h)[3];
    var e=(*h)[4]; var f=(*h)[5]; var g=(*h)[6]; var hh=(*h)[7];
    for (var i = 0u; i < 64u; i = i + 1u) {
        let S1 = rotr(e,6u) ^ rotr(e,11u) ^ rotr(e,25u);
        let ch = (e & f) ^ ((~e) & g);
        let t1 = hh + S1 + ch + K[i] + w[i];
        let S0 = rotr(a,2u) ^ rotr(a,13u) ^ rotr(a,22u);
        let maj = (a & b) ^ (a & c) ^ (b & c);
        let t2 = S0 + maj;
        hh=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    (*h)[0]=(*h)[0]+a; (*h)[1]=(*h)[1]+b; (*h)[2]=(*h)[2]+c; (*h)[3]=(*h)[3]+d;
    (*h)[4]=(*h)[4]+e; (*h)[5]=(*h)[5]+f; (*h)[6]=(*h)[6]+g; (*h)[7]=(*h)[7]+hh;
}

fn init_state() -> array<u32,8> {
    return array<u32,8>(0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
                        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u);
}

fn main_test(gid: u32) {
    // --- build name bytes (array of bytes, one per u32) ---
    var nb: array<u32, 64>;
    for (var i = 0u; i < 64u; i = i + 1u) { nb[i] = 0u; }
    var nlen = 0u;
    if (P.use_hash == 1u) { nb[0] = 0x23u; nlen = 1u; }          // '#'
    var t = gid;
    for (var j = 0u; j < P.inner_len; j = j + 1u) {              // low chars from gid
        nb[nlen + j] = charset[t % P.base];
        t = t / P.base;
    }
    for (var j = 0u; j < P.high_len; j = j + 1u) {               // fixed high chars
        nb[nlen + P.inner_len + j] = high_bytes[j];
    }
    nlen = nlen + P.name_len;

    // pad to a single 512-bit block (name always <= 55 bytes here)
    nb[nlen] = 0x80u;
    let bitlen = nlen * 8u;
    nb[62] = (bitlen >> 8u) & 0xffu;
    nb[63] = bitlen & 0xffu;
    var blk: array<u32,16>;
    for (var i = 0u; i < 16u; i = i + 1u) {
        blk[i] = (nb[4u*i] << 24u) | (nb[4u*i+1u] << 16u) | (nb[4u*i+2u] << 8u) | nb[4u*i+3u];
    }
    var h = init_state();
    compress(&h, &blk);
    // key = first 16 bytes = h[0..3]
    let k0 = h[0]; let k1 = h[1]; let k2 = h[2]; let k3 = h[3];

    // --- chash = SHA256(key)[0] ---
    var kb: array<u32,16>;
    for (var i = 0u; i < 16u; i = i + 1u) { kb[i] = 0u; }
    kb[0]=k0; kb[1]=k1; kb[2]=k2; kb[3]=k3;
    kb[4]=0x80000000u;
    kb[15]=128u;                                                 // 16 bytes * 8
    var hk = init_state();
    compress(&hk, &kb);
    let chash = (hk[0] >> 24u) & 0xffu;
    if (chash != P.target_chash) { return; }

    // --- HMAC-SHA256(secret = key||0^16, ciphertext) ---
    // inner = SHA256(ipad_block || ct_block); ipad = secret ^ 0x36
    var ipad: array<u32,16>;
    ipad[0]=k0 ^ 0x36363636u; ipad[1]=k1 ^ 0x36363636u;
    ipad[2]=k2 ^ 0x36363636u; ipad[3]=k3 ^ 0x36363636u;
    for (var i = 4u; i < 16u; i = i + 1u) { ipad[i] = 0x36363636u; }
    var hi = init_state();
    compress(&hi, &ipad);
    // inner = SHA256(ipad || ciphertext); the ct+padding blocks are baked in.
    /*INNER_TAIL*/            // hi = inner digest

    // outer = SHA256(opad_block || inner_digest)
    var opad: array<u32,16>;
    opad[0]=k0 ^ 0x5c5c5c5cu; opad[1]=k1 ^ 0x5c5c5c5cu;
    opad[2]=k2 ^ 0x5c5c5c5cu; opad[3]=k3 ^ 0x5c5c5c5cu;
    for (var i = 4u; i < 16u; i = i + 1u) { opad[i] = 0x5c5c5c5cu; }
    var ho = init_state();
    compress(&ho, &opad);
    var ob: array<u32,16>;
    ob[0]=hi[0]; ob[1]=hi[1]; ob[2]=hi[2]; ob[3]=hi[3];
    ob[4]=hi[4]; ob[5]=hi[5]; ob[6]=hi[6]; ob[7]=hi[7];
    ob[8]=0x80000000u;
    for (var i = 9u; i < 16u; i = i + 1u) { ob[i] = 0u; }
    ob[15]=768u;                                                 // (64+32) bytes * 8
    compress(&ho, &ob);
    let mac0 = (ho[0] >> 24u) & 0xffu;
    let mac1 = (ho[0] >> 16u) & 0xffu;
    if (mac0 != P.target_mac0 || mac1 != P.target_mac1) { return; }

    // hit — record gid (host reconstructs the name and confirms by decrypting)
    let slot = atomicAdd(&out_count, 1u);
    if (slot < arrayLength(&out_gids)) { out_gids[slot] = gid; }
}

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    let idx = gid.x + gid.y * P.stride_x;
    if (idx >= P.inner_count) { return; }
    main_test(idx);
}
