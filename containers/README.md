<!-- Waspid AI OS -->
# Docker Containers

Each folder here contains a Dockerfile, and a config.sh describing how to build
the images and where to push them. These images are built and pushed in GitHub Actions
by the `ghcr.yml` workflow.

The `waspid` image tag is the current Waspid runtime image — the name is
preserved to keep upstream SDK compatibility. Renaming the tag is a Tier-2
migration tracked separately.

## Building Manually

```bash
docker build -f containers/app/Dockerfile -t waspid .
docker build -f containers/sandbox/Dockerfile -t sandbox .
```
