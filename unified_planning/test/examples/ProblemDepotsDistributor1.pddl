(define (problem pddl-problem)
(:domain pddl-domain)
(:objects 
 crate0 crate1 - crate
 depot0 - depot
 distributor0 distributor1 - distributor
 pallet0 pallet1 pallet2 - pallet
 hoist0 hoist1 hoist2 - hoist
 truck0 truck1 - truck
)
(:shared-data
  (clear ?x - (either hoist surface))
  ((at ?t - truck) - place)
  ((pos ?c - crate) - (either place truck))
  ((on ?c - crate) - (either hoist truck surface)) - 
(either depot0 distributor0 truck0 truck1)
)
(:init
 (myAgent distributor1)
 (= (pos crate0) distributor0)
 (clear crate0)
 (= (on crate0) pallet1)
 (= (pos crate1) depot0)
 (clear crate1)
 (= (on crate1) pallet0)
 (= (at truck0) distributor1)
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
 (clear pallet2)
)
(:global-goal (and
 (= (on crate0) pallet2)
 (= (on crate1) pallet1)
))
)
