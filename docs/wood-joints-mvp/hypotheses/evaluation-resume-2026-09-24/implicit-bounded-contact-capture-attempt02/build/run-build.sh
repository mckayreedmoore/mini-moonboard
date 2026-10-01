#!/usr/bin/env bash
set -euo pipefail

packet_dir="$(cd "$(dirname "$0")/.." && pwd)"
context_dir="$packet_dir/build/context"
artifact_dir="$packet_dir/build/artifacts"
image_tag="mini-moonboard-fea:ccx-bounded-contact-capture-2.23-attempt02"
binary_name="ccx-bounded-contact-capture-2.23"

if docker image inspect "$image_tag" >/dev/null 2>&1; then
  echo "refusing to overwrite existing image tag: $image_tag" >&2
  exit 2
fi
if [[ -e "$artifact_dir" ]]; then
  echo "refusing to overwrite existing build artifacts: $artifact_dir" >&2
  exit 2
fi
docker build --pull=false --network=none --tag "$image_tag" "$context_dir"
image_id="$(docker image inspect "$image_tag" --format '{{.Id}}')"
mkdir -p "$artifact_dir"
container_id="$(docker create --entrypoint /bin/true "$image_tag")"
cleanup() { docker rm -f "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker cp "$container_id:/usr/local/bin/$binary_name" "$artifact_dir/$binary_name"
docker cp "$container_id:/opt/ccx-bounded-contact-capture/build-manifest.json" "$artifact_dir/build-manifest.json"
printf '%s\n' "$image_id" > "$artifact_dir/image-id.txt"
sha256sum "$artifact_dir/$binary_name" "$artifact_dir/build-manifest.json" "$artifact_dir/image-id.txt"
