# Practical FileMaker 19.5 script patterns

This directory contains five reusable, design-only patterns for FileMaker Pro
and FileMaker Server 19.5. They are reviewable design templates, not finished
scripts, Script IR documents, XML templates, or evidence that a script works in
FileMaker.

The machine-readable source of truth is
[`fm19.5/index.json`](fm19.5/index.json) plus each referenced `pattern.json`.
The adjacent README files explain those records for human reviewers. The index
contains only discovery metadata; it does not independently redefine a
pattern.

## Included patterns

1. [Validate a JSON script parameter](fm19.5/json-parameter-validation/README.md)
2. [Find one record by primary key](fm19.5/find-one-by-primary-key/README.md)
3. [Create a record and verify commit](fm19.5/create-record/README.md)
4. [Update a record and verify commit](fm19.5/update-record/README.md)
5. [Perform a server script and return JSON](fm19.5/perform-script-on-server/README.md)

No additional patterns are implied by this collection.

## How an AI must use the patterns

1. Decompose the requested work into the five available patterns.
2. Fix the execution context as `client`, `psos`, or `server_schedule`.
3. Check every selected step against the `fms19` compatibility catalog.
4. Resolve every `partial` condition and reject `unknown` or `unavailable`
   support.
5. Enumerate every required FileMaker object.
6. Resolve every required placeholder from target-solution metadata or an
   explicit requirement.
7. Finalize the input and output JSON contracts.
8. Design both the success path and every relevant error branch.
9. Review concurrency, record locks, retries, and idempotency.
10. Check renderer status separately from compatibility.

If any required placeholder remains unresolved, stop at a draft design. Do not
emit a completed script, invent an object name, or invent an internal FileMaker
ID.

## Evidence boundary

Every pattern has `verificationStatus: "design_only"`. Repository validation,
unit tests, and documentation review establish only that the design data is
internally consistent with the normalized compatibility catalog. They do not
establish FileMaker Pro 19.5 paste or runtime evidence, FileMaker Server 19.5
FMSE evidence, or XML renderer support.

The patterns are repository design assets and are intentionally not installed
in the Python wheel. The current CLI does not expose or execute them, and
shipping them as runtime package data would create an unsupported public
runtime API. Read them from the repository until a separately reviewed pattern
API is defined.

## Shared result contract

The five patterns refer to
[`fm19.5/common-result.schema.json`](fm19.5/common-result.schema.json). A result
always has `ok`, `code`, `message`, `data`, `error`, and `meta`. Pattern README
files provide synthetic success and failure examples.
