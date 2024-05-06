(define (domain parking)
 (:requirements :strips :typing :durative-actions)
 (:types car curb)
 (:predicates 
    (at-curb ?car - car) 
    (at-curb-num ?car - car ?curb - curb)
    (behind-car ?car ?front-car - car)
    (car-clear ?car - car) 
    (curb-clear ?curb - curb)
 )

 (:functions (total-cost))
	(:durative-action move-curb-to-curb
		:parameters (?car - car ?curbsrc ?curbdest - curb)
		:duration (= ?duration 1)
		:condition (and 
			(at start (car-clear ?car))
			(at start (curb-clear ?curbdest))
			(at start (at-curb-num ?car ?curbsrc))
		)
		:effect (and 
			(at start (not (curb-clear ?curbdest)))
			(at end (curb-clear ?curbsrc))
			(at end (at-curb-num ?car ?curbdest))
			(at start (not (at-curb-num ?car ?curbsrc)))
			(at end (increase (total-cost) 1))
		)
	)

	(:durative-action move-curb-to-car
		:parameters (?car - car ?curbsrc - curb ?cardest - car)
		:duration (= ?duration 2)
		:condition (and 
			(at start (car-clear ?car))
			(at start (car-clear ?cardest))
			(at start (at-curb-num ?car ?curbsrc))
			(at start (at-curb ?cardest)) 
		)
		:effect (and 
			(at start (not (car-clear ?cardest)))
			(at end (curb-clear ?curbsrc))
			(at end (behind-car ?car ?cardest))
			(at start (not (at-curb-num ?car ?curbsrc)))
			(at start (not (at-curb ?car)))
			(at end (increase (total-cost) 2))
		)
	)

	(:durative-action move-car-to-curb
		:parameters (?car - car ?carsrc - car ?curbdest - curb)
		:duration (= ?duration 2)
		:condition (and 
			(at start (car-clear ?car))
			(at start (curb-clear ?curbdest))
			(at start (behind-car ?car ?carsrc))
		)
		:effect (and 
			(at start (not (curb-clear ?curbdest)))
			(at end (car-clear ?carsrc))
			(at end (at-curb-num ?car ?curbdest))
			(at start (not (behind-car ?car ?carsrc)))
			(at end (at-curb ?car))
			(at end (increase (total-cost) 2))
		)
	)

	(:durative-action move-car-to-car
		:parameters (?car - car ?carsrc - car ?cardest - car)
		:duration (= ?duration 3)
		:condition (and 
			(at start (car-clear ?car))
			(at start (car-clear ?cardest))
			(at start (behind-car ?car ?carsrc))
			(at start (at-curb ?cardest))
		)
		:effect (and 
			(at start (not (car-clear ?cardest)))
			(at end (car-clear ?carsrc))
			(at end (behind-car ?car ?cardest))
			(at start (not (behind-car ?car ?carsrc)))
			(at end (increase (total-cost) 3))
		)
	)
)

