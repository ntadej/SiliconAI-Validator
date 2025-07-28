LABEL org.opencontainers.image.source https://github.com/ntadej/SiliconAI-Validator
LABEL org.opencontainers.image.description "SiliconAI-Validator ACTS container image"

FROM ghcr.io/acts-project/spack-container:13_linux-ubuntu24.04-x86_64_gcc-13.3.0

COPY dependencies/ACTS /opt/acts-source
COPY docker/build.sh /opt/build.sh

RUN chmod +x /opt/build.sh \
 && bash -c "/opt/build.sh" \
 && rm -rf /opt/build.sh
