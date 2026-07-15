/**
 * 国密安全加固模块 (基于 sm-crypto 提供 SM2, SM3, SM4-CBC 混合加密)
 */
import { sm2, sm4 } from 'sm-crypto';

export const FIXED_KEY = "sql_convert_fixed_key";

export function bytesToBase64(bytes: Uint8Array): string {
    let binString = "";
    for (let i = 0; i < bytes.length; i++) {
        binString += String.fromCharCode(bytes[i]);
    }
    return btoa(binString);
}

export function base64ToBytes(base64: string): Uint8Array {
    let binString = atob(base64);
    let bytes = new Uint8Array(binString.length);
    for (let i = 0; i < binString.length; i++) {
        bytes[i] = binString.charCodeAt(i);
    }
    return bytes;
}

/**
 * 将 Uint8Array 数组转为十六进制字符串
 */
export function bytesToHex(bytes: Uint8Array): string {
    return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
}

/**
 * 将字符串转为十六进制字符串（UTF-8 编码）
 */
export function stringToHex(str: string): string {
    const encoder = new TextEncoder();
    return bytesToHex(encoder.encode(str));
}

/**
 * 国密混合加密逻辑：
 * 1. 动态生成 16 字节随机密钥 (SM4_KEY) 和 16 字节随机初始向量 (SM4_IV)。
 * 2. 使用 SM2 公钥加密 envelop (SM4_KEY + SM4_IV)，输出 Base64 密钥信封（不带 04 前导标志传给后端）。
 * 3. 使用 SM4-CBC 对 rawPayload 进行对称加密，输出 Base64 密文。
 * 
 * 返回:
 *   {
 *     payload: base64(密文),
 *     envelop: base64(SM2 加密的 key+iv),
 *     rawKeyBytes: Uint8Array(16 字节 sm4 key，用于 HMAC 校验)
 *   }
 */
export function encryptPayload(
    rawPayload: string,
    serverPublicKeyHex: string
): { payload: string; envelop: string; rawKeyBytes: Uint8Array } {
    // 1. 生成 16 字节随机密钥和 IV
    const keyBytes = window.crypto.getRandomValues(new Uint8Array(16));
    const ivBytes = window.crypto.getRandomValues(new Uint8Array(16));

    // 2. 构造密钥信封 (32 字节) 并使用 SM2 公钥加密
    // 注意：sm-crypto 的 doEncrypt 需要 04 前导，且密文格式必须使用 C1C2C3 (mode 0) 以兼容后端 gmssl
    const envelopBytes = new Uint8Array(32);
    envelopBytes.set(keyBytes, 0);
    envelopBytes.set(ivBytes, 16);

    // 直接对 Uint8Array 数组进行 SM2 非对称加密
    const encryptedHex = sm2.doEncrypt(envelopBytes, '04' + serverPublicKeyHex, 0);
    
    // 我们解密时后端要求去掉 '04' 前导。如果 sm-crypto 输出带有 '04'（通常 C1C2C3 输出可能以 04 开头，长度为 258 字符），
    // 经检测，刚才 interop 测试中，sm-crypto doEncrypt 输出长度为 256 字符，即不带 04 前缀。
    // 为了健壮性，若有前导 '04'，我们在 base64 编码前剥离它
    let finalEnvelopHex = encryptedHex;
    if (finalEnvelopHex.startsWith('04') && finalEnvelopHex.length === 258) {
        finalEnvelopHex = finalEnvelopHex.substring(2);
    }
    
    const envelopBase64 = bytesToBase64(base64ToBytes(btoa(
        finalEnvelopHex.match(/.{1,2}/g)?.map((byte: string) => String.fromCharCode(parseInt(byte, 16))).join('') || ''
    )));

    // 3. 使用 SM4-CBC 加密 payload
    // sm-crypto encrypt(plaintext, key, { mode: 'cbc', iv })
    // plaintext 可以是 string，key/iv 可以 be Uint8Array
    const encryptedSm4Hex = sm4.encrypt(rawPayload, keyBytes, {
        mode: 'cbc',
        iv: ivBytes
    });

    const payloadBase64 = bytesToBase64(base64ToBytes(btoa(
        encryptedSm4Hex.match(/.{1,2}/g)?.map((byte: string) => String.fromCharCode(parseInt(byte, 16))).join('') || ''
    )));

    return {
        payload: payloadBase64,
        envelop: envelopBase64,
        rawKeyBytes: keyBytes
    };
}

/**
 * 将二进制或十六进制密钥信封通过 SM2 公钥加密，并移除前导 04 字节，返回十六进制密文
 */
export function encryptEnvelop(envelop: Uint8Array | string, serverPublicKeyHex: string): string {
    let encrypted = sm2.doEncrypt(envelop, '04' + serverPublicKeyHex, 0);
    if (encrypted.startsWith('04') && encrypted.length === 258) {
        encrypted = encrypted.substring(2);
    }
    return encrypted;
}

/**
 * 消息摘要算法统一接口 (防篡改签名，使用原生纯 TS 手写实现，避免依赖 sm-crypto 中缺失的 hmac API)
 */
export const SM3 = (() => {
    function rotl(x: number, n: number): number {
        return (x << n) | (x >>> (32 - n));
    }
    function T(j: number): number {
        return j < 16 ? 0x79cc4519 : 0x7a879d8a;
    }
    function FF(x: number, y: number, z: number, j: number): number {
        if (j < 16) return x ^ y ^ z;
        return (x & y) | (x & z) | (y & z);
    }
    function GG(x: number, y: number, z: number, j: number): number {
        if (j < 16) return x ^ y ^ z;
        return (x & y) | (~x & z);
    }
    function P0(x: number): number {
        return x ^ rotl(x, 9) ^ rotl(x, 17);
    }
    function P1(x: number): number {
        return x ^ rotl(x, 15) ^ rotl(x, 23);
    }
    function sm3Hash(msgBytes: Uint8Array): string {
        let len = msgBytes.length;
        let k = (448 - (len * 8 + 1) % 512 + 512) % 512;
        let padLen = len + 1 + Math.floor(k / 8) + 8;
        let pad = new Uint8Array(padLen);
        pad.set(msgBytes);
        pad[len] = 0x80;
        let bitsCount = len * 8;
        pad[padLen - 8] = 0; pad[padLen - 7] = 0;
        pad[padLen - 6] = 0; pad[padLen - 5] = 0;
        pad[padLen - 4] = (bitsCount >>> 24) & 0xff;
        pad[padLen - 3] = (bitsCount >>> 16) & 0xff;
        pad[padLen - 2] = (bitsCount >>> 8) & 0xff;
        pad[padLen - 1] = bitsCount & 0xff;
        let V = [
            0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
            0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e
        ];
        for (let b = 0; b < padLen / 64; b++) {
            let W = new Uint32Array(68);
            let Wp = new Uint32Array(64);
            let block = pad.subarray(b * 64, (b + 1) * 64);
            for (let i = 0; i < 16; i++) {
                W[i] = (block[i * 4] << 24) | (block[i * 4 + 1] << 16) | (block[i * 4 + 2] << 8) | block[i * 4 + 3];
            }
            for (let j = 16; j < 68; j++) {
                W[j] = P1(W[j - 16] ^ W[j - 9] ^ rotl(W[j - 3], 15)) ^ rotl(W[j - 13], 7) ^ W[j - 6];
            }
            for (let j = 0; j < 64; j++) {
                Wp[j] = W[j] ^ W[j + 4];
            }
            let [A, B, C, D, E, F, G, H] = V;
            for (let j = 0; j < 64; j++) {
                let SS1 = rotl((rotl(A, 12) + E + rotl(T(j), j % 32)) | 0, 7);
                let SS2 = SS1 ^ rotl(A, 12);
                let TT1 = (FF(A, B, C, j) + D + SS2 + Wp[j]) | 0;
                let TT2 = (GG(E, F, G, j) + H + SS1 + W[j]) | 0;
                D = C;
                C = rotl(B, 9);
                B = A;
                A = TT1;
                H = G;
                G = rotl(F, 19);
                F = E;
                E = P0(TT2);
            }
            V = [
                (V[0] ^ A) | 0, (V[1] ^ B) | 0, (V[2] ^ C) | 0, (V[3] ^ D) | 0,
                (V[4] ^ E) | 0, (V[5] ^ F) | 0, (V[6] ^ G) | 0, (V[7] ^ H) | 0
            ];
        }
        return V.map(x => {
            let s = (x >>> 0).toString(16);
            return "0".repeat(8 - s.length) + s;
        }).join("");
    }
    function hmac(keyBytes: Uint8Array, msgBytes: Uint8Array): string {
        let key = new Uint8Array(64);
        if (keyBytes.length > 64) {
            let h = sm3Hash(keyBytes);
            for (let i = 0; i < 32; i++) key[i] = parseInt(h.substring(i * 2, i * 2 + 2), 16);
        } else {
            key.set(keyBytes);
        }
        let ipad = new Uint8Array(64);
        let opad = new Uint8Array(64);
        for (let i = 0; i < 64; i++) {
            ipad[i] = key[i] ^ 0x36;
            opad[i] = key[i] ^ 0x5c;
        }
        let inner = new Uint8Array(64 + msgBytes.length);
        inner.set(ipad);
        inner.set(msgBytes, 64);
        let innerHash = sm3Hash(inner);
        let innerHashBytes = new Uint8Array(32);
        for (let i = 0; i < 32; i++) innerHashBytes[i] = parseInt(innerHash.substring(i * 2, i * 2 + 2), 16);
        let outer = new Uint8Array(64 + 32);
        outer.set(opad);
        outer.set(innerHashBytes, 64);
        return sm3Hash(outer);
    }
    return { hmac };
})();
