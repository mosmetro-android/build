#!/usr/bin/env bash

set -e

BRANCH_NAME=$DRONE_BRANCH

BUILD_NUMBER=$(jq -r '.branches[$branch].build' builds-data/data.json --arg branch "$BRANCH_NAME")
[ "$BUILD_NUMBER" ] || BUILD_NUMBER=0
BUILD_NUMBER=$((BUILD_NUMBER+1))

VERSION=$(grep versionCode app/build.gradle | grep -Eo '[0-9]*?')
OUTPUT="bin/MosMetro-$BRANCH_NAME-b$BUILD_NUMBER"

echo "Starting build #$BUILD_NUMBER of branch $BRANCH_NAME..."
export BRANCH_NAME BUILD_NUMBER
gradle build

[ -e bin ] && rm -r bin; mkdir -p bin
mv "$(find . -name '*-unsigned.apk')" "$OUTPUT-unsigned.apk"

echo "Signing APK..."
echo "$KEYSTORE" | base64 -d > keystore.jks
$ANDROID_SDK_ROOT/build-tools/*/apksigner sign \
  --ks-key-alias pw.thedrhax.* \
  --ks keystore.jks \
  --ks-pass env:PASS_KEYSTORE \
  --key-pass env:PASS_KEY \
  --in "$OUTPUT-unsigned.apk" \
  --out "$OUTPUT.apk"
rm keystore.jks

echo "Creating changelog"
echo -en "Сборка $BRANCH_NAME-#$BUILD_NUMBER:\n\n" > "$OUTPUT.txt"
git log --reverse --pretty=oneline $DRONE_COMMIT_BEFORE..$DRONE_COMMIT_AFTER \
  | cut -d\  -f 2- \
  | sed 's/^/* /g' \
  | tee -a "$OUTPUT.txt"

echo "Publishing"

function jqi {
  TMPFILE=$(mktemp)
  jq "$@" > "$TMPFILE"
  mv "$TMPFILE" "$2"
}

OLD_APK=$(jq -r '.branches[$branch].filename' builds-data/data.json --arg branch "$BRANCH_NAME")
if [ "$OLD_APK" != "null" ]; then
  rm "builds-data/apks/$OLD_APK"
fi
unset OLD_APK

mv "$OUTPUT.apk" "builds-data/apks/"

jqi '
  . + $config.static |

  ("MosMetro-" + $branch + "-b" + ($build | tostring) + ".apk") as $filename |

  .branches[$branch] = {
    name: $branch,
    description: (.branches[$branch].description // ""),
    version: $version,
    build: $build,
    by_build: true,
    url: ($config.base_url + "/apks/" + $filename),
    filename: $filename,
    stable: ($config.stable_branches | contains([$branch])),
    message: $changelog
  }
' builds-data/data.json \
  --argfile config builds-master/config.json \
  --arg branch "$BRANCH_NAME" \
  --argjson version "$VERSION" \
  --argjson build "$BUILD_NUMBER" \
  --rawfile changelog "$OUTPUT.txt"

pushd builds-data > /dev/null
git add .
git commit -m "Build $BRANCH_NAME-#$BUILD_NUMBER"
popd > /dev/null
