(define (problem depotprob7512)
(:domain depot)
(:objects
 depot0 - depot
 distributor0 distributor1 - distributor
 truck0 truck1 - truck
 crate0 crate1 crate2 crate3 - crate
 pallet0 pallet1 pallet2 - pallet
 hoist0 hoist1 hoist2 - hoist
)
(:shared-data
  (clear ?x - (either surface hoist))
  ((at ?t - truck) - place)
  ((pos ?c - crate) - (either place truck))
  ((on ?c - crate) - (either surface hoist truck)) - 
(either depot0 distributor0 distributor1 truck1)
)
(:init
 (myAgent truck0)
 (= (pos crate0) depot0)
 (clear crate0)
 (= (on crate0) pallet0)
 (= (pos crate1) distributor1)
 (not (clear crate1))
 (= (on crate1) pallet2)
 (= (pos crate2) distributor1)
 (clear crate2)
 (= (on crate2) crate1)
 (= (pos crate3) distributor0)
 (clear crate3)
 (= (on crate3) pallet1)
 (= (at truck0) depot0)
 (= (at truck1) depot0)
 (= (located hoist0) depot0)
 (clear hoist0)
 (= (located hoist1) distributor0)
 (clear hoist1)
 (= (located hoist2) distributor1)
 (clear hoist2)
 (= (placed pallet0) depot0)
 (not (clear pallet0))
 (= (placed pallet1) distributor0)
 (not (clear pallet1))
 (= (placed pallet2) distributor1)
 (not (clear pallet2))
)
(:global-goal (and
 (= (on crate0) pallet2)
 (= (on crate1) crate3)
 (= (on crate2) pallet0)
 (= (on crate3) pallet1)
))
)
