#!/usr/bin/env bash
set -euo pipefail

packet_dir="$(cd "$(dirname "$0")/.." && pwd)"
context_dir="$packet_dir/build/context"
artifact_dir="$packet_dir/build/artifacts"
base_tag="mini-moonboard-fea:ccx-upstream-2.23-v1"
locked_base_tag="mini-moonboard-fea:ccx-upstream-2.23-v1-attempt04-lock"
image_tag="mini-moonboard-fea:ccx-bounded-contact-capture-2.23-attempt04"
binary_name="ccx-bounded-contact-capture-2.23-attempt04"

if [[ -e "$artifact_dir" ]]; then
  echo "refusing to overwrite build artifacts: $artifact_dir" >&2
  exit 2
fi
for tag in "$locked_base_tag" "$image_tag"; do
  if docker image inspect "$tag" >/dev/null 2>&1; then
    echo "refusing to overwrite existing image tag: $tag" >&2
    exit 2
  fi
done

expected_base_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["image_id"])' "$context_dir/base-image-pin.json")"
resolved_base_id="$(docker image inspect "$base_tag" --format '{{.Id}}')"
if [[ "$resolved_base_id" != "$expected_base_id" ]]; then
  echo "base image ID mismatch: expected=$expected_base_id resolved=$resolved_base_id" >&2
  exit 2
fi

# Pin the already-resolved local image behind a one-use build tag so the FROM
# reference cannot silently follow a changed public/local base tag mid-build.
docker tag "$resolved_base_id" "$locked_base_tag"
locked_id="$(docker image inspect "$locked_base_tag" --format '{{.Id}}')"
if [[ "$locked_id" != "$resolved_base_id" ]]; then
  docker image rm "$locked_base_tag" >/dev/null 2>&1 || true
  echo "locked base tag does not resolve to the preflight image ID" >&2
  exit 2
fi

mkdir -p "$artifact_dir"
cleanup() {
  if [[ -n "${container_id:-}" ]]; then docker rm -f "$container_id" >/dev/null 2>&1 || true; fi
  docker image rm "$locked_base_tag" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker build --pull=false --network=none \
  --build-arg "BASE_IMAGE=$locked_base_tag" \
  --build-arg "CCX_BASE_IMAGE_ID=$resolved_base_id" \
  --tag "$image_tag" "$context_dir"
built_image_id="$(docker image inspect "$image_tag" --format '{{.Id}}')"
container_id="$(docker create --entrypoint /bin/true "$image_tag")"
docker cp "$container_id:/usr/local/bin/$binary_name" "$artifact_dir/$binary_name"
docker cp "$container_id:/opt/ccx-bounded-contact-capture/build-manifest.json" "$artifact_dir/build-manifest.json"
python3 "$packet_dir/build/record_build_provenance.py" \
  "$expected_base_id" "$resolved_base_id" "$built_image_id" "$locked_base_tag" \
  "$image_tag" "$packet_dir"
sha256sum "$artifact_dir/$binary_name" "$artifact_dir/build-manifest.json" \
  "$artifact_dir/build-provenance.json"
