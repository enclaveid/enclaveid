FROM bitnami/azure-cli:2.59.0

WORKDIR /

# TODO: package version pinning
USER root
RUN install_packages openssl gnutls-bin xxd

USER 1001

COPY entrypoint.sh /entrypoint.sh
COPY ca.cnf /ca.cnf

ENTRYPOINT ["/entrypoint.sh"]
