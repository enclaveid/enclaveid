FROM envoyproxy/envoy@sha256:6ef8ffb00949be3adc064e117bf5560f2e64077be025b5e6f82121038c11c8eb

COPY envoy.yaml etc/envoy/envoy.yaml

RUN chmod go+r /etc/envoy/envoy.yaml

CMD ["/usr/local/bin/envoy", "-c", "/etc/envoy/envoy.yaml"]
