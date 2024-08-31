import { useState, useEffect } from 'react';
import {
  decodeAttestation,
  getExpectedMesaurements,
} from '../../utils/attestation/awsNitro';
import { trpc } from '../../utils/trpc';
import { useGoWasm } from '../useGoWasm';
import {
  getEnclaveCryptoKey,
  getPublicKeyHashBrowser,
  parsePublicKey,
} from '../../utils/crypto/asymmetricBrowser';
import toast from 'react-hot-toast';

export function useAwsNitroAttestation(): {
  publicKey: CryptoKey | null;
  error: Error | null;
} {
  const [publicCryptoKey, setPublicCryptoKey] = useState<CryptoKey | null>(
    null,
  );
  const [error, setError] = useState<Error | null>(null);
  const { isReady: isWasmReady, error: wasmError } =
    useGoWasm('./nitrite.wasm');

  const { expectedNonce, expectedPcr0 } = getExpectedMesaurements();

  const attestationQuery = trpc.public.getAttestation.useQuery({
    nonce: expectedNonce,
  });

  const { base64Cbor, publicKey } = attestationQuery.data ?? {};

  useEffect(() => {
    if (wasmError) {
      console.error('WASM error', wasmError);
      setError(wasmError);
    }
  }, [wasmError]);

  useEffect(() => {
    async function runAttestation() {
      try {
        // Validate the signature and decode the attestation document
        const { result: validationResult, error: validationError } = JSON.parse(
          // This one's coming from WASM
          window.validateAttestation(
            base64Cbor,
            true, //TODO: don't validate anything for now, later on use the dev flag: import.meta.env.DEV
          ),
        );
        if (validationError !== '') throw new Error(validationError);

        // Validate the attestation contents
        const { pcr0, nonce, b64PublicKeyDigest } =
          decodeAttestation(validationResult);

        if (nonce !== expectedNonce) {
          throw new Error(
            `Invalid nonce value: ${nonce}. Expected: ${expectedNonce}`,
          );
        }

        if (pcr0 !== expectedPcr0) {
          throw new Error(
            `Invalid PCR0 value: ${pcr0}. Expected: ${expectedPcr0}`,
          );
        }

        const publicKeyBuffer = await parsePublicKey(publicKey);

        const expectedb64PublicKeyDigest =
          await getPublicKeyHashBrowser(publicKeyBuffer);

        if (b64PublicKeyDigest !== expectedb64PublicKeyDigest) {
          throw new Error(
            `Invalid public key digest value: ${b64PublicKeyDigest}. Expected: ${expectedb64PublicKeyDigest}`,
          );
        }

        const cryptoKey = await getEnclaveCryptoKey(publicKeyBuffer);

        setPublicCryptoKey(cryptoKey);
      } catch (e) {
        if (e instanceof Error) {
          setError(e);
        }

        throw e;
      }
    }
    if (isWasmReady && base64Cbor && publicKey) {
      const promise = runAttestation();

      toast.promise(promise, {
        loading: 'Running attestation...',
        success: 'Attestation successful',
        error: 'Attestation failed',
      });
    }
  }, [base64Cbor, expectedNonce, expectedPcr0, isWasmReady, publicKey]);

  return { publicKey: publicCryptoKey, error };
}
