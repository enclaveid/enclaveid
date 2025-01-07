# Verification

In order to independently verify the confidentiality of the system, the following assets need to be checked:

- The Kata policy measurement
- The image digests in the Kata policy
- The frontend code on IPFS

You can run `./verify.sh` from the root of the repository to check each of them.

## Kata policy measurement

`make helm-chart` will render the Helm chart into two separate files, one pertaining the Kata specific configuration and the other the rest of the cluster.

`az confcom...` will take the Kata config and produce a policy measurment, which should match the one in the attestation report.

## Image digests in the Kata policy

All container images are built with Kaniko using the `--reproducible` flag, so that the SHAs are deterministic.

In the Helm chart, the images are referenced by their SHAs, binding the code to the attestation report.

The script will build all images and check that the SHAs match the ones in the Kata spcific configuration rendered before.

## Frontend code on IPFS

This one is easy: build the frontend from the repo release and compare the file hashes with the ones on IPFS.
