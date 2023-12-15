(define (problem depotprob1818) (:domain Depot)
(:objects
	depot0 - depot
	distributor0 distributor1 - distributor
	truck0 truck1 - truck
	pallet0 pallet1 pallet2 - pallet
	crate0 crate1 - crate
	hoist0 hoist1 hoist2 - hoist)
(:init
	(at pallet0 depot0)
	(clear crate1)
	(at pallet1 distributor0)
	(clear crate0)
	(at pallet2 distributor1)
	(clear pallet2)
	(at truck0 distributor1)
	(= (speed truck0) 4)
	(at truck1 depot0)
	(= (speed truck1) 8)
	(at hoist0 depot0)
	(available hoist0)
	(= (power hoist0) 2)
	(at hoist1 distributor0)
	(available hoist1)
	(= (power hoist1) 8)
	(at hoist2 distributor1)
	(available hoist2)
	(= (power hoist2) 6)
	(at crate0 distributor0)
	(on crate0 pallet1)
	(= (weight crate0) 12)
	(at crate1 depot0)
	(on crate1 pallet0)
	(= (weight crate1) 86)
	(= (distance depot0 depot0) 0)
	(= (distance depot0 distributor0) 5)
	(= (distance depot0 distributor1) 7)
	(= (distance distributor0 depot0) 5)
	(= (distance distributor0 distributor0) 0)
	(= (distance distributor0 distributor1) 5)
	(= (distance distributor1 depot0) 4)
	(= (distance distributor1 distributor0) 4)
	(= (distance distributor1 distributor1) 0)
)

(:goal (and
		(on crate0 pallet2)
		(on crate1 pallet1)
	)
)

;(:metric minimize (total-time))
)
