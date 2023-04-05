(define (problem depot-problem)
 (:domain depot-domain)
 (:objects
   depot0_place distributor0_place distributor1_place - place
   crate0 crate1 - crate
   truck0 truck1 - truck
   hoist0 hoist1 hoist2 - hoist
   pallet0 pallet1 pallet2 - pallet
   depot0_agent - depot0_agent_type
   distributor0_agent - distributor0_agent_type
   distributor1_agent - distributor1_agent_type
   driver0_agent - driver0_agent_type
   driver1_agent - driver1_agent_type
 )
 (:init
  (at_ pallet0 depot0_place)
  (clear crate1)
  (at_ pallet1 distributor0_place)
  (clear crate0)
  (at_ pallet2 distributor1_place)
  (clear pallet2)
  (at_ truck0 distributor1_place)
  (at_ truck1 depot0_place)
  (at_ hoist0 depot0_place)
  (at_ hoist1 distributor0_place)
  (at_ hoist2 distributor1_place)
  (at_ crate0 distributor0_place)
  (on crate0 pallet1)
  (at_ crate1 depot0_place)
  (on crate1 pallet0)
  (a_pos driver0_agent distributor1_place)
  (a_pos driver1_agent depot0_place)
  (a_pos depot0_agent depot0_place)
  (a_pos distributor0_agent distributor0_place)
  (a_pos distributor1_agent distributor1_place)
  (a_driving driver0_agent truck0))
 (:goal (and (on crate0 pallet2) (on crate1 pallet1)))
)