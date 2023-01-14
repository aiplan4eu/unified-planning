(define (domain citycar)
(:requirements :typing :equality :negative-preconditions :action-costs :conditional-effects)
  (:types
	car
	junction
	garage
	road
	)

  (:predicates
    (same_line ?xy - junction ?xy2 - junction) ;; junctions in line (row)
    (diagonal ?x - junction ?y - junction ) ;; junctions in diagonal (on the map)
    (at_car_jun ?c - car ?x - junction) ;; a car is at the junction
    (at_car_road ?c - car ?x - road) ;; a car is in a road
    (starting ?c - car ?x - garage) ;; a car is in its initial position
    (arrived ?c - car ?x - junction) ;; a car arrived at destination
    (road_connect ?r1 - road ?xy - junction ?xy2 - junction) ;; there is a road that connects 2 junctions
    (clear ?xy - junction ) ;; the junction is clear
    (in_place ?x - road) ;; the road has been put in place
    (at_garage ?g - garage ?xy - junction ) ;; position of the starting garage

  )
(:functions (total-cost) - number)

;; move the car in a road: no limit on the number of cars on the road
(:action move_car_in_road
  :parameters (?xy_initial - junction ?xy_final - junction ?machine - car ?r1 - road)
  :precondition (and
		(at_car_jun ?machine ?xy_initial)
		(road_connect ?r1 ?xy_initial ?xy_final)
		(in_place ?r1)
		)
  :effect (and
		(clear ?xy_initial)
		(at_car_road ?machine ?r1)
		(not (at_car_jun ?machine ?xy_initial) )
		(increase (total-cost) 1)
		)
)

;; move the car out of the road to a junction. Junction must be clear.
(:action move_car_out_road
  :parameters (?xy_initial - junction ?xy_final - junction ?machine - car ?r1 - road)
  :precondition (and
		(at_car_road ?machine ?r1)
		(clear ?xy_final)
		(road_connect ?r1 ?xy_initial ?xy_final)
		(in_place ?r1)
		)
  :effect (and
		(at_car_jun ?machine ?xy_final)
		(not (clear ?xy_final))
		(not (at_car_road ?machine ?r1) )
		(increase (total-cost) 1)
		)
)

;; car in the final position. They are removed from the network and position is cleared.
(:action car_arrived
  :parameters (?xy_final - junction ?machine - car )
  :precondition (and
		(at_car_jun ?machine ?xy_final)
		)
  :effect (and
		(clear ?xy_final)
		(arrived ?machine ?xy_final)
		(not (at_car_jun ?machine ?xy_final))
		)
)

;; car moved from the initial garage in the network.
(:action car_start
  :parameters (?xy_final - junction ?machine - car ?g - garage)
  :precondition (and
		(at_garage ?g ?xy_final)
		(starting ?machine ?g)
		(clear ?xy_final)
		)
  :effect (and
		(not (clear ?xy_final))
		(at_car_jun ?machine ?xy_final)
		(not (starting ?machine ?g))
		)
)

;; build diagonal road
(:action build_diagonal_oneway
  :parameters (?xy_initial - junction ?xy_final - junction ?r1 - road)
  :precondition (and
		(clear ?xy_final)
		(not (in_place ?r1))
		(diagonal ?xy_initial ?xy_final)
		)
  :effect (and
		(road_connect ?r1 ?xy_initial ?xy_final)
		(in_place ?r1)
                (increase (total-cost) 30)
		)
)

;; build straight road
(:action build_straight_oneway
  :parameters (?xy_initial - junction ?xy_final - junction ?r1 - road)
  :precondition (and
		(clear ?xy_final)
		(same_line ?xy_initial ?xy_final)
		(not (in_place ?r1))
		)
  :effect (and
		(road_connect ?r1 ?xy_initial ?xy_final)
		(in_place ?r1)
                (increase (total-cost) 20)
		)
)

;; remove a road
(:action destroy_road
  :parameters (?xy_initial - junction ?xy_final - junction ?r1 - road)
  :precondition (and
		(road_connect ?r1 ?xy_initial ?xy_final)
		(in_place ?r1)
		)
  :effect (and
		(not (in_place ?r1))
		(not (road_connect ?r1 ?xy_initial ?xy_final))
                (increase (total-cost) 10)
		(forall (?c1 - car)
                     (when (at_car_road ?c1 ?r1)
			(and
			  (not (at_car_road ?c1 ?r1))
			  (at_car_jun ?c1 ?xy_initial)
			)
		      )
		   )
		)
)




)
