# Original editing examples

These examples demonstrate meaning preservation. They are original examples, not dictionary-verified conformity specimens.

## Software procedure

Source:

> Once you've confirmed that the backup has completed, utilize `atlasctl migrate --dry-run` to check the migration and, if it returns exit code 0, execute `atlasctl migrate`; otherwise don't proceed.

Draft:

1. Make sure that the backup is complete.
2. Run `atlasctl migrate --dry-run`.
3. If the exit code is 0, run `atlasctl migrate`.
4. If the exit code is not 0, stop the procedure.

The commands, prerequisite, and branch condition stay intact. “Run” and “migration” still need a vocabulary review for a full conformity claim.

## Research description

Source:

> Our preliminary simulator results suggest that this approach may reduce errors, but we haven't evaluated the method on physical hardware.

Draft:

> The initial simulator results suggest a possible decrease in errors with this method. We have not tested the method on physical hardware.

Keep the benefit uncertain and the evidence limited to the simulator. Never change a possible benefit into a measured hardware result. Check the vocabulary before a conformity claim.

## Exact UI text

Source:

> Click “Force Sync” to retry; this doesn't delete your saved files.

Draft:

> Select **Force Sync** to try again. This action does not delete your saved files.

The label remains **Force Sync** because the reader must find that exact label in the product.

## Ambiguous instruction

Source:

> Disconnect it after it stops.

Do not invent what “it” refers to. Ask which component the reader must disconnect and what must stop first.

## Meaning before a preferred word

Source:

> The operator may cancel the update. The operator must cancel the update if the checksum is incorrect.

Preserve the difference between permission and obligation. Preserve the checksum condition. Do not replace both sentences with “Cancel the update.”
