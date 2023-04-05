(define (domain ma_logistic-domain)
 (:requirements :factored-privacy :typing)
 (:types
    object_ driver1_type driver2_type driver3_type - object
    location city vehicle package - object_
    truck airplane - vehicle
    airport - location
 )
 (:constants
   truck_ - truck
   loc loc_from loc_to - location
   city_ - city
   obj - package
 )
 (:predicates
 (at_ ?object - object_ ?location - location)
  (on ?object - object_)
  (in ?package - package ?vehicle - vehicle)
  (:private
   (a_pos ?agent - driver1_type ?location - location)
   (a_in_city ?agent - driver1_type ?location - location ?city - city)
   (a_driving ?agent - driver1_type ?truck - truck)))
 (:action drive_truck
  :parameters ( ?driver1 - driver1_type)
  :precondition (and 
   (at_ truck_ loc_from)
   (a_in_city ?driver1 loc_from city_)
   (a_in_city ?driver1 loc_to city_)
   (a_driving ?driver1 truck_)
   (a_pos ?driver1 loc_from)
  )
  :effect (and
   (not (a_pos ?driver1 loc_from))
   (not (at_ truck_ loc_from))
   (at_ truck_ loc_to)
   (a_pos ?driver1 loc_to)
))
 (:action unload_truck
  :parameters ( ?driver1 - driver1_type)
  :precondition (and 
   (at_ truck_ loc)
   (in obj truck_)
   (a_pos ?driver1 loc)
  )
  :effect (and
   (not (in obj truck_))
   (at_ obj loc)
))
 (:action load_truck
  :parameters ( ?driver1 - driver1_type)
  :precondition (and 
   (at_ truck_ loc)
   (at_ obj loc)
   (a_pos ?driver1 loc)
  )
  :effect (and
   (not (at_ obj loc))
   (in obj truck_)
))
)
