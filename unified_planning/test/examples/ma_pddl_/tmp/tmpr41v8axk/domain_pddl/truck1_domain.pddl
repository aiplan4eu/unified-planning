(define (domain ma_logistic-domain)
 (:requirements :factored-privacy :typing)
 (:types
    object_ truck1_type truck2_type airplane_type - object
    location city package vehicle - object_
    truck_ airplane_ - vehicle
    airport - location
 )
 (:constants
   loc_to loc_from loc - location
   city_ - city
   obj - package
 )
 (:predicates
 (at_ ?object - object_ ?location - location)
  (in ?package - package ?vehicle - vehicle)
  (:private
   (a_pos ?agent - truck1_type ?location - location)
   (a_in_city ?agent - truck1_type ?location - location ?city - city)
   (a_on ?agent - truck1_type ?object - object_)))
 (:action drive_truck
  :parameters ( ?truck1 - truck1_type)
  :precondition (and 
   (a_pos ?truck1 loc_from)
   (a_in_city ?truck1 loc_from city_)
   (a_in_city ?truck1 loc_to city_)
  )
  :effect (and
   (not (a_pos ?truck1 loc_from))
   (a_pos ?truck1 loc_to)
))
 (:action unload_truck
  :parameters ( ?truck1 - truck1_type)
  :precondition (and 
   (a_pos ?truck1 loc)
   (a_on ?truck1 obj)
  )
  :effect (and
   (not (a_on ?truck1 obj))
   (at_ obj loc)
))
 (:action load_truck
  :parameters ( ?truck1 - truck1_type)
  :precondition (and 
   (at_ obj loc)
   (a_pos ?truck1 loc)
  )
  :effect (and
   (not (at_ obj loc))
   (a_on ?truck1 obj)
))
)
