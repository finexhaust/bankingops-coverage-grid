# Verified historical release snapshots

This archive supplies the immutable evidence needed to validate existing
historical overlays and synthetic scenarios without network access or Git
history. It does not change any release, mapping, admission or review status.

`index.json` pins the original published manifest file digest, canonical manifest
digest and declared source commit for each retained release. Manifest files were
downloaded from the corresponding GitHub release asset on 4 November 2026.
Their byte digests matched the GitHub release-asset metadata. Every artifact in
each complete original manifest was checked against its declared Git commit;
all 65 v0.6.2 artifacts and all 68 v0.6.3 artifacts matched in size and SHA-256.

The retained subset contains the operating catalogue, task concepts, coverage
matrix and control-point definitions used by the validators. These files are
byte-for-byte copies from those verified release commits. Other artifacts in
the complete manifest are not silently substituted from the current checkout.
Requests for absent artifacts fail.

The authoritative v0.6.2 release manifest is the published asset, with canonical
digest `67f491ec4068af0949c36c4f8679f2a4a8a63f759ea19c39e51f0bd6e29b2554`
and commit `c84bebfa55081b061431357ad59fec4d93f2925c`. The embedded manifest
at the old tag was stale and is deliberately not used.

`tools/release_snapshots.py` verifies manifest structure, identity, aggregate and
self digests, unique safe artifact paths, and the size and digest of every loaded
artifact. A tag resolves only through this explicit index. Unknown or malformed
pins fail; an empty archive or shallow checkout never disables verification.
An exact consumer-supplied manifest digest can also select a schema-valid,
self-consistent local manifest, whose requested artifact bytes are verified.

Adding a release requires its published manifest, an explicit immutable index
entry and verified artifact bytes. New release manifests include the archive
itself, making this dependency available to downstream consumers.
