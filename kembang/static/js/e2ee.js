/* ============================================================================
   e2ee.js — Modul enkripsi end-to-end buat fitur Chat Desa.

   PRINSIP: semua enkripsi/dekripsi terjadi DI BROWSER pakai Web Crypto
   API bawaan (bukan library eksternal — gak butuh CDN, gak ada supply
   chain risk tambahan). Server cuma nyimpen ciphertext, IV, dan AES key
   yang sudah dibungkus (wrapped) pakai public key penerima. Server
   tidak pernah pegang plaintext pesan atau private key siapapun.

   SKEMA (hybrid encryption, mirip PGP):
   - Tiap pesan dienkripsi pakai AES-256-GCM key acak yang unik per-pesan.
   - AES key itu lalu "dibungkus" 2x pakai RSA-OAEP: sekali pakai public
     key warga, sekali pakai public key Kantor Desa — supaya warga dan
     staff kantor sama-sama bisa buka pesannya sendiri, siapapun yang
     ngirim duluan.
   - Private key warga: disimpan di IndexedDB browser warga.
   - Private key Kantor Desa: disimpan di server, TAPI dalam keadaan
     terbungkus (wrapped) pakai passphrase kantor yang cuma diketahui
     staff (PBKDF2 + AES-GCM). Server nyimpen blob terenkripsi ini
     doang, gak pernah tau passphrase-nya.

   BATASAN (baca ini, jangan asal klaim "sama kayak WhatsApp" ke user):
   - Ini bukan Signal Protocol. Gak ada forward secrecy / key ratchet —
     kalau private key bocor suatu saat, chat lama yang direkam bisa
     dibuka. Trade-off wajar buat skala chat layanan desa, mirip skema
     email terenkripsi (PGP), bukan messaging protocol tercanggih.
   - Siapapun staff yang tau passphrase kantor bisa baca SEMUA chat
     desa (bukan cuma yang dia tangani) — ini disengaja karena chat
     didesain sebagai kotak masuk kantor bersama.
   - Passphrase kantor GAK ADA cara reset. Lupa = histori chat desa
     hilang selamanya. Simpan baik-baik (mis. di password manager tim).
   ============================================================================ */

const RSA_PARAMS = {
  name: "RSA-OAEP",
  modulusLength: 2048,
  publicExponent: new Uint8Array([1, 0, 1]),
  hash: "SHA-256",
};
const PBKDF2_ITERATIONS = 210000;

// ---------------------------------------------------------------- util ----

function bufToB64(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)));
}
function b64ToBuf(b64) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return arr.buffer;
}

// ---------------------------------------------------- keypair & storage ----

async function generateKeypair() {
  return crypto.subtle.generateKey(RSA_PARAMS, true, ["encrypt", "decrypt"]);
}

async function exportPublicKeyJwk(keyPair) {
  return crypto.subtle.exportKey("jwk", keyPair.publicKey);
}

// IndexedDB minimal, cuma buat nyimpen satu private key milik user
// yang sedang login di browser ini.
const DB_NAME = "e2ee_store";
const STORE_NAME = "keys";

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE_NAME);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbSet(key, value) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(value, key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function idbGet(key) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const req = tx.objectStore(STORE_NAME).get(key);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => reject(req.error);
  });
}

async function storeMyPrivateKey(privateKey) {
  await idbSet("private_key", privateKey);
}
async function getMyPrivateKey() {
  return idbGet("private_key");
}

// ---------------------------------------------------- recovery code ----
// String acak buat dicetak/ditulis tangan sekali pas setup, dipakai
// kalau petugas lupa passphrase harian. Alfabet sengaja buang karakter
// yang gampang ketuker pas ditulis tangan (0/O, 1/I/L).

const RECOVERY_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";

function generateRecoveryCode() {
  const groups = [];
  for (let g = 0; g < 5; g++) {
    let group = "";
    const randomBytes = crypto.getRandomValues(new Uint8Array(4));
    for (const b of randomBytes) group += RECOVERY_ALPHABET[b % RECOVERY_ALPHABET.length];
    groups.push(group);
  }
  return groups.join("-"); // contoh: XK9M-2PQR-7WCF-...-....
}

// ------------------------------------- backup/restore private key ----
// Opsional, dipakai kalau mau bikin fitur "export key" buat warga yang
// ganti device. Private key dibungkus pakai passphrase pilihan warga
// sendiri (BEDA dari passphrase kantor), aman disimpan/diunduh sebagai
// file backup karena tanpa passphrase gak ada gunanya.

async function wrapPrivateKeyWithPassphrase(privateKey, passphrase) {
  const jwk = await crypto.subtle.exportKey("jwk", privateKey);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const baseKey = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(passphrase), "PBKDF2", false, ["deriveKey"]
  );
  const aesKey = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    baseKey, { name: "AES-GCM", length: 256 }, false, ["encrypt"]
  );
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv }, aesKey, new TextEncoder().encode(JSON.stringify(jwk))
  );

  return {
    ciphertext: bufToB64(ciphertext),
    iv: bufToB64(iv),
    salt: bufToB64(salt),
    iterations: PBKDF2_ITERATIONS,
  };
}

async function unwrapPrivateKeyWithPassphrase(wrapped, passphrase) {
  const baseKey = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(passphrase), "PBKDF2", false, ["deriveKey"]
  );
  const aesKey = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: b64ToBuf(wrapped.salt), iterations: wrapped.iterations, hash: "SHA-256" },
    baseKey, { name: "AES-GCM", length: 256 }, false, ["decrypt"]
  );
  // salah passphrase -> decrypt lempar error, biarkan nyampe ke caller
  const plainBuf = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: b64ToBuf(wrapped.iv) }, aesKey, b64ToBuf(wrapped.ciphertext)
  );
  const jwk = JSON.parse(new TextDecoder().decode(plainBuf));
  return crypto.subtle.importKey("jwk", jwk, RSA_PARAMS, true, ["decrypt"]);
}

// ------------------------------------------- enkripsi/dekripsi pesan ----

/**
 * @param plaintext string isi pesan
 * @param recipientPublicKeysJwk { warga: jwk, desa: jwk }
 */
async function encryptMessage(plaintext, recipientPublicKeysJwk) {
  const aesKey = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv }, aesKey, new TextEncoder().encode(plaintext)
  );
  const rawAesKey = await crypto.subtle.exportKey("raw", aesKey);

  const wrapped = {};
  for (const [label, jwk] of Object.entries(recipientPublicKeysJwk)) {
    const pubKey = await crypto.subtle.importKey("jwk", jwk, RSA_PARAMS, false, ["encrypt"]);
    const wrappedKey = await crypto.subtle.encrypt({ name: "RSA-OAEP" }, pubKey, rawAesKey);
    wrapped[label] = bufToB64(wrappedKey);
  }

  return {
    ciphertext: bufToB64(ciphertext),
    iv: bufToB64(iv),
    wrapped_key_warga: wrapped.warga,
    wrapped_key_desa: wrapped.desa,
  };
}

/**
 * @param msg { ciphertext, iv } (base64) — biasanya objek pesan dari server
 * @param myPrivateKey CryptoKey privat milikku
 * @param myWrappedKeyB64 wrapped_key_warga ATAU wrapped_key_desa, tergantung siapa yang baca
 */
async function decryptMessage(msg, myPrivateKey, myWrappedKeyB64) {
  const rawAesKey = await crypto.subtle.decrypt(
    { name: "RSA-OAEP" }, myPrivateKey, b64ToBuf(myWrappedKeyB64)
  );
  const aesKey = await crypto.subtle.importKey("raw", rawAesKey, { name: "AES-GCM" }, false, ["decrypt"]);
  const plainBuf = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: b64ToBuf(msg.iv) }, aesKey, b64ToBuf(msg.ciphertext)
  );
  return new TextDecoder().decode(plainBuf);
}

window.E2EE = {
  generateKeypair,
  exportPublicKeyJwk,
  storeMyPrivateKey,
  getMyPrivateKey,
  generateRecoveryCode,
  wrapPrivateKeyWithPassphrase,
  unwrapPrivateKeyWithPassphrase,
  encryptMessage,
  decryptMessage,
};