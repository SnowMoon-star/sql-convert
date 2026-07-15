import axios from 'axios';
import { useAuthStore } from '../store/auth';
import { SM3, encryptPayload, bytesToBase64, base64ToBytes, encryptEnvelop } from './crypto';

const textEncoder = new TextEncoder();

// 全局缓存的服务端 SM2 公钥
let serverPublicKey: string | null = null;

/**
 * 确保加载了服务端的 SM2 公钥，避免重复拉取
 */
async function ensurePublicKey(): Promise<string> {
  if (serverPublicKey) {
    return serverPublicKey;
  }
  // 必须直接使用基础 axios 实例请求，避免请求拦截器引发死循环
  const resp = await axios.get('/api/crypto/key');
  if (resp.data && resp.data.public_key) {
    serverPublicKey = resp.data.public_key;
    return serverPublicKey!;
  }
  throw new Error('无法拉取服务端的国密公钥。');
}

const request = axios.create({
  baseURL: '',
  timeout: 60000,
});

request.interceptors.request.use(
  async (config) => {
    const authStore = useAuthStore();
    const isLogin = config.url === '/api/login';

    if (isLogin) {
      authStore.clearToken();
    }

    // 仅针对非 GET 请求进行国密混合加密和防篡改签名
    if (config.method && config.method.toUpperCase() !== 'GET' && config.url !== '/api/crypto/key') {
      try {
        const pubKey = await ensurePublicKey();
        const timestamp = Date.now().toString();
        const nonce = Math.random().toString(36).substring(2);

        if (!config.data) {
          config.data = {};
        }

        if (config.data instanceof FormData) {
          // 1. 文件上传场景：不加密大文件 Body，但动态产生一次性对称秘钥用于签名和密钥交换
          const keyBytes = window.crypto.getRandomValues(new Uint8Array(16));
          const ivBytes = window.crypto.getRandomValues(new Uint8Array(16));
          
          // 加密密钥信封
          const envelopBytes = new Uint8Array(32);
          envelopBytes.set(keyBytes, 0);
          envelopBytes.set(ivBytes, 16);
          // 直接加密 Uint8Array 二进制字节密钥信封
          let encryptedHex = encryptEnvelop(envelopBytes, pubKey);
          
          const envelopBase64 = bytesToBase64(base64ToBytes(btoa(
            encryptedHex.match(/.{1,2}/g)?.map((byte: string) => String.fromCharCode(parseInt(byte, 16))).join('') || ''
          )));

          const payloadToSign = `${config.url}:${timestamp}:${nonce}`;
          
          config.headers['X-Encrypted-Key'] = envelopBase64;
          config.headers['X-Signature'] = SM3.hmac(keyBytes, textEncoder.encode(payloadToSign));
          config.headers['X-Timestamp'] = timestamp;
          config.headers['X-Nonce'] = nonce;
        } else {
          // 2. 普通 JSON 请求场景：实施 SM4-CBC + SM2 + SM3 混合加密
          let rawBody = config.data;
          if (typeof rawBody === 'object') {
            rawBody = JSON.stringify(rawBody);
          }

          // 核心混合加密：产生信封及密文
          const { payload, envelop, rawKeyBytes } = encryptPayload(rawBody, pubKey);

          config.data = { payload: payload };
          config.headers['Content-Type'] = 'application/json';
          config.headers['X-Encrypted-Key'] = envelop;

          const payloadToSign = `${config.url}:${timestamp}:${nonce}:${payload}`;
          config.headers['X-Signature'] = SM3.hmac(rawKeyBytes, textEncoder.encode(payloadToSign));
          config.headers['X-Timestamp'] = timestamp;
          config.headers['X-Nonce'] = nonce;
        }
      } catch (err) {
        console.error('[Crypto] 混合加密失败:', err);
        return Promise.reject(err);
      }
    }

    if (authStore.token) {
      config.headers['Authorization'] = `Bearer ${authStore.token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);



request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const authStore = useAuthStore();
    if (error.response) {
      const status = error.response.status;
      if (status === 401) {
        authStore.clearToken();
        const isLoginPath = window.location.pathname.endsWith('/login') || window.location.hash.includes('/login');
        if (!isLoginPath) {
          window.location.href = '#/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default request;
