# Evidence and failure boundaries

A run contains configuration, explicit geometry, proposed currents, complete case records, source-file hashes and an unsigned output manifest. `verify` recomputes the manifest hashes and rejects escaping paths or mismatched bytes.

`audit` goes beyond byte integrity: it recomputes the primary training/validation fields and gates from archived paths and proposals. Its test deliberately changes a reported metric and updates the manifest, then confirms the recomputation catches the forged result. It does not rerun the optimizer, authenticate observations, validate external solvers or replay all uncertainty samples.

A file hash proves integrity only relative to the manifest being trusted. Anyone able to replace both an artifact and its manifest can replace the record. There are no private signing keys, authenticated telemetry, trusted timestamps or provenance attestations. The hash is not numerical validation.

Source hashes identify the executed package files. They do not hash the whole interpreter, CPU, BLAS implementation or every environment dependency. Runtime versions and a resolved Python dependency inventory are supplied separately. Reproducibility means the tested tolerances and decisions reproduce; floating-point results and compressed archives are not promised bitwise identical across platforms.

Fault injections and Gaussian uncertainty are disclosed simulated inputs. They are not sensor observations. The training grid is visible to optimization; the offset grid is withheld. Passing both grids does not bound continuous-volume error or detect all unsampled harmonics. Tight stress cases are retained even when the solver fails.

The optimizer can request an infeasible or unconverged step. Every proposed result is rechecked, and the campaign records held-out failures separately. Unavailable channels are removed from the response basis rather than silently receiving commands. Saturation can prevent correction even with a full unbounded column space.

No executable path sends current settings, energizes a driver, changes a reactor state, connects to a controller or interprets an external PASS label as validated physics. CSV currents are research proposals. All physical hardware quantities belong to an unbuilt proposal or unresolved functional inventory.
