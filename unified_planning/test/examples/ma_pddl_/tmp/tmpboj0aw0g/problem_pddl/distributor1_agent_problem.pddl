(define (problem depot-problem)
 (:domain depot-domain)
 (:objects
   truck0 truck1 - truck
   depot0_place distributor0_place distributor1_place - place
   hoist0 hoist1 hoist2 - hoist
   crate0 crate1 - crate
   pallet0 pallet1 pallet2 - pallet
   depot0_agent - depot0_agent_type
   distributor0_agent - distributor0_agent_type
   distributor1_agent - distributor1_agent_type
   driver0_agent - driver0_agent_type
   driver1_agent - driver1_agent_type
 )
 (:init
  (a------------------_at_ ?distributor1_agent pallet0 depot0_place)
  (a------------------_clear ?distributor1_agent crate1)
  (a------------------_at_ ?distributor1_agent pallet1 distributor0_place)
  (a------------------_clear ?distributor1_agent crate0)
  (a------------------_at_ ?distributor1_agent pallet2 distributor1_place)
  (a------------------_clear ?distributor1_agent pallet2)
  (a------------------_at_ ?distributor1_agent truck0 distributor1_place)
  (a------------------_at_ ?distributor1_agent truck1 depot0_place)
  (a------------------_at_ ?distributor1_agent hoist0 depot0_place)
  (a------------------_at_ ?distributor1_agent hoist1 distributor0_place)
  (a------------------_at_ ?distributor1_agent hoist2 distributor1_place)
  (a------------------_at_ ?distributor1_agent crate0 distributor0_place)
  (a------------------_on ?distributor1_agent crate0 pallet1)
  (a------------------_at_ ?distributor1_agent crate1 depot0_place)
  (a------------------_on ?distributor1_agent crate1 pallet0)
  (a_available distributor1_agent hoist2)
  (a_pos distributor1_agent distributor1_place))
 (:goal (and (a------------------_on ?distributor1_agent crate0 pallet2) (a------------------_on ?distributor1_agent crate1 pallet1)))
)