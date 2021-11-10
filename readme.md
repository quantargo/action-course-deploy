#  Deploy courses to quantargo.com/courses

This repository is a GitHub Action to deploy interactive programming courses to the Quantargo course platform.

Learn more about building your own interactive programming courses in the [official documentation](https://quantargo.com/docs/02-courses)

## Publishing new releases
Similar to the pattern used by GitHub's own actions, the latest commit should be marked as v1:

``` bash
# Remove the v1 tag from the remote
git push origin :refs/tags/v1

# Recreate the v1 tag on the latest commit locally
git tag -fa v1

# Push commits and tags to the remote
git push --follow-tags
```
