# Terminal outcome of the extended transient pilot

The parent runtime bound stopped the native process after
2408.047770 seconds. The execution status is `bounded_timeout`
and the native process return code is 137 after the stop grace. This was an
explicit runtime stop, not completion of the requested 0.025 s step.
[execution.json](execution.json) has SHA-256 `b2092585ac3910fc209a01d4f123c80703be9556ae3b0c336f5fb6c41ad38d10`.

Eight increments converged, ending at 0.003129826 s. The final complete
relative displacement q is 1.19207456e-5 mm; maximum loaded-node displacement
is 9.53164063e-6 mm and maximum controller rotation is 5.73958433e-9 rad.
None of the sampled motion limits was exceeded. Increment 9 was still
iterating when the run stopped; its trial output is not an accepted sample.

Increment 2 required two rejected attempts. The third attempt reduced the
time increment, restored original contact stiffness at iteration 7, and
converged at iteration 20. Later accepted increment iteration counts are
12, 7, 6, 8, 6 and 22. This establishes recovery under the original contact
law and convergence controls, but does not establish rapid or monotone
convergence as the response advances.

The parent verified the input-freeze hash, all fourteen frozen input hashes
and all twelve recorded output hashes after termination. This terminal note
was added after that output inventory was captured and is not one of those
twelve recorded outputs. Preserve the recorded outputs unchanged.

The first increment still crosses the force-ramp knots and has the known
forcing-impulse quadrature error. This run does not take up the bolt-hole
clearances, establish joint stiffness or capacity, or close any structural
criterion. The next prepared comparison aligns integration endpoints to the
ramp knots and raises the reference load for a bounded seating diagnostic;
its time, contact-penalty and engagement sensitivities remain necessary.

Raw native outputs are retained locally with their hashes in the execution
record. They are not a complete published runnable bundle.
