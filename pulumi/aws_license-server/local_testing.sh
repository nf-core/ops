#!/usr/bin/env bash

# NOTE If this fails run `op signin` to flip to nf-core
export SENTIEON_LICSRVR_IP=$(op read "op://Dev/SENTIEON_LICSRVR_IP/IP")
export SENTIEON_LICSRVR_PORT=$(op read "op://Dev/SENTIEON_LICSRVR_IP/Port")

nextflow secrets set SENTIEON_LICENSE_BASE64 $(echo -n "$SENTIEON_LICSRVR_IP:$SENTIEON_LICSRVR_PORT"| base64 -w 0)
# nextflow secrets set SENTIEON_AUTH_MECH_BASE64 ${{ secrets.SENTIEON_AUTH_MECH_BASE64 }}
SENTIEON_ENCRYPTION_KEY=$(op read "op://Dev/SENTIEON_ENCRYPTION_KEY/password")
SENTIEON_LICENSE_MESSAGE=$(op read "op://Dev/SENTIEON_LICENSE_MESSAGE/password")
SENTIEON_AUTH_DATA=$(python3 tests/modules/nf-core/sentieon/license_message.py encrypt --key "$SENTIEON_ENCRYPTION_KEY" --message "$SENTIEON_LICENSE_MESSAGE")
SENTIEON_AUTH_DATA_BASE64=$(echo -n "$SENTIEON_AUTH_DATA" | base64 -w 0)
nextflow secrets set SENTIEON_AUTH_DATA_BASE64 $SENTIEON_AUTH_DATA_BASE64


curl -L https://s3.amazonaws.com/sentieon-release/software/sentieon-genomics-202308.02.tar.gz | tar -zxf -
./sentieon-genomics-202308.02/bin/sentieon licclnt ping -s 63.33.204.94:8990 || (echo "Ping Failed"; exit 1)
