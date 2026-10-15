#!/usr/bin/env bash
#
# Submit an artifact to Apple's notary service, wait for the verdict,
# print the full log on failure, and staple the ticket on success.
#
# Usage:
#   setup/macos/notarize.sh <path-to-.app-or-.dmg>
#
# Required environment variables:
#   NOTARY_APPLE_ID   Apple ID email with access to the developer team
#   NOTARY_PASSWORD   app-specific password for that Apple ID
#   NOTARY_TEAM_ID    Apple Developer Team ID
#
set -euo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ] || [ ! -e "$TARGET" ]; then
    echo "ERROR: notarize.sh requires an existing target path" >&2
    exit 1
fi

: "${NOTARY_APPLE_ID:?NOTARY_APPLE_ID not set}"
: "${NOTARY_PASSWORD:?NOTARY_PASSWORD not set}"
: "${NOTARY_TEAM_ID:?NOTARY_TEAM_ID not set}"

AUTH=(--apple-id "$NOTARY_APPLE_ID" --password "$NOTARY_PASSWORD" --team-id "$NOTARY_TEAM_ID")

# notarytool accepts .zip, .dmg and .pkg. An .app must be zipped first;
# a .dmg is submitted as-is.
case "$TARGET" in
    *.app)
        SUBMIT="${TARGET%.app}.notarize.zip"
        rm -f "$SUBMIT"
        /usr/bin/ditto -c -k --keepParent "$TARGET" "$SUBMIT"
        ;;
    *)
        SUBMIT="$TARGET"
        ;;
esac

echo "Submitting '$SUBMIT' to the notary service ..."
SUBMISSION_ID=$(
    xcrun notarytool submit "$SUBMIT" "${AUTH[@]}" --output-format json \
        | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])"
)
echo "Submission ID: $SUBMISSION_ID"

# Block until the submission reaches a terminal state.
xcrun notarytool wait "$SUBMISSION_ID" "${AUTH[@]}"

STATUS=$(
    xcrun notarytool info "$SUBMISSION_ID" "${AUTH[@]}" --output-format json \
        | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])"
)
echo "Notarization status: $STATUS"

if [ "$STATUS" != "Accepted" ]; then
    echo "Notarization was not accepted — full log follows:" >&2
    xcrun notarytool log "$SUBMISSION_ID" "${AUTH[@]}" >&2 || true
    exit 1
fi

echo "Stapling ticket to '$TARGET' ..."
xcrun stapler staple "$TARGET"
xcrun stapler validate "$TARGET"
echo "Notarization and stapling complete for '$TARGET'."
