#!/bin/bash

# Builds, signs and optionally notarizes novelWriter.app.
# "Release" signs with the Developer ID and notarizes, "Debug" is ad-hoc signed.
# Prepare the keychain and the notarytool profile before running a Release build.

set -euo pipefail

application_sign_cert="Developer ID Application: Headbright Group VOF (MS6MBBXCFJ)"
credential_profile="headbright-signs"

configuration="${1:-Release}"
src_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
dist_dir="$src_dir/dist_macos"
app_bundle="$dist_dir/novelWriter.app"

case "$configuration" in
    Release) identity="$application_sign_cert" ;;
    Debug) identity="" ;;
    *) echo "unknown configuration '$configuration' (expected Release or Debug)"; exit 2 ;;
esac

arch=$(uname -m)
if [[ $arch == "arm64" ]]; then
    arch="aarch64"
fi

cd "$src_dir"
version=$(uv run --no-sync pkgutils.py version)
archive="$dist_dir/novelwriter-${version}-${arch}.zip"

echo "## PyInstaller build ($configuration) of novelWriter $version"
PYINSTALLER_STRICT_BUNDLE_CODESIGN_ERROR=1 \
    uv run --no-sync pkgutils.py build-mac ${identity:+--identity "$identity"}

echo "### Verifying signature"
codesign --verify --deep --strict --verbose=2 "$app_bundle"

echo "### Creating archive"
ditto -c -k --keepParent "$app_bundle" "$archive"

if [[ $configuration == "Release" ]]; then
    echo "### Submitting for notarization"
    if ! xcrun notarytool submit "$archive" --keychain-profile "$credential_profile" \
        ${NW_KEYCHAIN:+--keychain "$NW_KEYCHAIN"} --wait
    then
        echo "Notarization failed"
        echo "use 'xcrun notarytool log <submission-id> --keychain-profile \"$credential_profile\"' for more detail"
        exit 1
    fi
    echo "### Stapling"
    xcrun stapler staple "$app_bundle"
    xcrun stapler validate "$app_bundle"
    rm -f "$archive"
    ditto -c -k --keepParent "$app_bundle" "$archive"
fi

(cd "$dist_dir" && shasum -a 256 "$(basename "$archive")" | tee "$(basename "$archive").sha256")

echo "### Size"
du -sh "$app_bundle"
ls -lh "$archive"
