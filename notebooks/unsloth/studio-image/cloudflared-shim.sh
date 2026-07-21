#!/bin/sh
# cloudflared wrapper shim
# ---------------------------------------------------------------------------
# Forces cloudflared onto the IPv4 edge on hosts with broken IPv6 egress
# (Radeon Cloud / AnRui). Without this, cloudflared resolves AAAA records
# first, tries its tunnel-create POST + edge discovery over IPv6, hangs, and
# times out -> "Cloudflare tunnel: requested but failed to start".
#
# Idempotent: if the caller already passed --edge-ip-version, we don't add it.
REAL="/usr/local/bin/cloudflared.real"

for a in "$@"; do
    case "$a" in
        --edge-ip-version|--edge-ip-version=*)
            exec "$REAL" "$@"
            ;;
    esac
done

exec "$REAL" --edge-ip-version 4 "$@"
