
(define (domain logistics_cont)
  (:requirements :strips :equality :typing :conditional-effects :disjunctive-preconditions :contingent)
  (:types OBJ TRUCK LOCATION AIRPLANE CITY AIRPORT )
  (:predicates 	(at_tl ?obj - TRUCK  ?loc - LOCATION)
		(at_ta ?obj - TRUCK  ?loc - AIRPORT)
		(at_aa ?obj - AIRPLANE ?loc - AIRPORT)
		(at_ol ?obj - OBJ ?loc - LOCATION)
		(at_oa ?obj - OBJ ?loc - AIRPORT)
		(in_ot ?obj1 - OBJ ?obj2 - TRUCK)
		(in_oa ?obj1 - OBJ ?obj2 - AIRPLANE)
		(in_city_l ?loc - LOCATION ?city - CITY)
		(in_city_a ?loc - AIRPORT ?city - CITY)
		(in_city_t ?loc - TRUCK ?city - CITY))


(:action sense_package_loc_t
 :parameters (?obj - OBJ ?loc - LOCATION ?truck - TRUCK)
 :precondition (at_tl ?truck ?loc)
 :observe (at_ol ?obj ?loc))

(:action sense_package_ap_t
 :parameters (?obj - OBJ ?loc - AIRPORT ?truck - TRUCK)
 :precondition (at_ta ?truck ?loc)
 :observe (at_oa ?obj ?loc))

(:action sense_package_ap_a
 :parameters (?obj - OBJ ?loc - AIRPORT ?airplane - AIRPLANE)
 :precondition (at_aa ?airplane ?loc)
 :observe (at_oa ?obj ?loc))


(:action LOAD_TRUCK_LOC
  :parameters
   (?obj - OBJ
    ?truck - TRUCK
    ?loc - LOCATION
    ?city - CITY)
  :precondition
   (and
	(at_tl ?truck ?loc)
 	(in_city_t ?truck ?city)
	(in_city_l ?loc ?city)
  	(at_ol ?obj ?loc)
   )
  :effect
   (and (not (at_ol ?obj ?loc))
	  (in_ot ?obj ?truck)))

(:action LOAD_TRUCK_AP
  :parameters
   (?obj - OBJ
    ?truck - TRUCK
    ?loc - AIRPORT
    ?city - CITY)
  :precondition
   (and
	(at_ta ?truck ?loc)
 	(in_city_t ?truck ?city)
	(in_city_a ?loc ?city)
	(at_oa ?obj ?loc)

   )
  :effect (and (not (at_oa ?obj ?loc))
	  (in_ot ?obj ?truck)))

(:action LOAD_AIRPLANE
  :parameters
   (?obj - OBJ ?airplane - AIRPLANE ?loc - AIRPORT)
  :precondition
   (and (at_aa ?airplane ?loc) (at_oa ?obj ?loc))
  :effect
   (and (not (at_oa ?obj ?loc))
              (in_oa ?obj ?airplane)))

(:action UNLOAD_TRUCK_LOC
  :parameters
   (?obj - OBJ
    ?truck - TRUCK
    ?loc - LOCATION
    ?city - CITY)
  :precondition
   (and
	(at_tl ?truck ?loc)
	(in_city_t ?truck ?city)
	(in_city_l ?loc ?city)(in_ot ?obj ?truck)
        ;(not (at_ol ?obj ?loc))
   )
  :effect
  	 (and (not (in_ot ?obj ?truck))
              (at_ol ?obj ?loc)))

(:action UNLOAD_TRUCK_AP
  :parameters
   (?obj - OBJ
    ?truck - TRUCK
    ?loc - AIRPORT
    ?city - CITY)
  :precondition
   (and
	(at_ta ?truck ?loc)
	(in_city_t ?truck ?city)
	(in_city_a ?loc ?city)
(in_ot ?obj ?truck)
        ;(not (at_ol ?obj ?loc))
   )
  :effect
	 (and (not (in_ot ?obj ?truck))
              (at_oa ?obj ?loc)))

(:action UNLOAD_AIRPLANE
  :parameters
   (?obj - OBJ
    ?airplane - AIRPLANE
    ?loc - AIRPORT)
  :precondition
  (and (at_aa ?airplane ?loc)	(in_oa ?obj ?airplane)   )
  :effect
 	 (and (not (in_oa ?obj ?airplane))
              (at_oa ?obj ?loc)))

(:action DRIVE_TRUCK_LOC_AP
  :parameters
   (?truck - TRUCK
    ?loc1 - LOCATION
    ?loc2 - AIRPORT
    ?city - CITY)
  :precondition
   (and (at_tl ?truck ?loc1)
        (in_city_l ?loc1 ?city)
        (in_city_a ?loc2 ?city)
	(in_city_t ?truck ?city)
	;(not (at_ta ?truck ?loc2))
   )
  :effect
   (and (not (at_tl ?truck ?loc1))
        (at_ta ?truck ?loc2)))

(:action DRIVE_TRUCK_AP_LOC
  :parameters
   (?truck - TRUCK
    ?loc1 - AIRPORT
    ?loc2 - LOCATION
    ?city - CITY)
    :precondition
   (and (at_ta ?truck ?loc1)
        (in_city_a ?loc1 ?city)
        (in_city_l ?loc2 ?city)
	(in_city_t ?truck ?city)
	;(not (at_tl ?truck ?loc2))
   )
  :effect
   (and (not (at_ta ?truck ?loc1))
        (at_tl ?truck ?loc2)))

(:action FLY_AIRPLANE
  :parameters
   (?airplane - AIRPLANE
    ?loc1 - AIRPORT
    ?loc2 - AIRPORT)
  :precondition
  (and
	(at_aa ?airplane ?loc1)
	;(not (at ?airplane ?loc2)
  )
  :effect
   (and (not (at_aa ?airplane ?loc1) )
        (at_aa ?airplane ?loc2 )))
)
