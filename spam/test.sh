#!/usr/bin/env bash

set -eu

if [[ -z ${DEBUG+x} ]]; then
    debug=echo
else
    debug=:
fi

. ../ip.conf

sed -i "1 s/.*/$domain, www.$domain {/" Caddyfile
