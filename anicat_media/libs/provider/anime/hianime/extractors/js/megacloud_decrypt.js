const CryptoJS = require("crypto-js");

/**
 * Extracts a secret key from an encrypted string based on an array of index pairs,
 * then uses that key to decrypt the rest of the string.
 * @param {string} encryptedString - The full encrypted sources string.
 * @param {string} varsJson - A JSON string representing an array of [start, length] pairs.
 * @returns {string} The decrypted JSON string of video sources.
 */
function getSecretAndDecrypt(encryptedString, varsJson) {
  const values = JSON.parse(varsJson);
  let secret = "";
  let encryptedSource = "";
  let encryptedSourceArray = encryptedString.split("");
  let currentIndex = 0;

  for (const index of values) {
    const start = index[0] + currentIndex;
    const end = start + index[1];

    for (let i = start; i < end; i++) {
      secret += encryptedString[i];
      encryptedSourceArray[i] = "";
    }
    currentIndex += index[1];
  }

  encryptedSource = encryptedSourceArray.join("");

  const decrypted = CryptoJS.AES.decrypt(encryptedSource, secret).toString(
    CryptoJS.enc.Utf8,
  );
  return decrypted;
}

// Main execution logic
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error(
    "Usage: node megacloud_decrypt.js <encryptedString> '<varsJson>'",
  );
  process.exit(1);
}

const encryptedString = args[0];
const varsJson = args[1];

try {
  const result = getSecretAndDecrypt(encryptedString, varsJson);
  // The result is already a JSON string of the sources, just print it to stdout.
  console.log(result);
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
