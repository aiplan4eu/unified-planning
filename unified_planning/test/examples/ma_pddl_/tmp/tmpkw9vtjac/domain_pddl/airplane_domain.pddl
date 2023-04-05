(define (domain ma_logistic-domain)
 (:requirements :factored-privacy :typing)
 (:types
    object_ truck1_type truck2_type airplane_type - object
    location city package vehicle - object_
    truck_ airplane_ - vehicle
    airport - location
 )
 (:constants
   obj - package
   loc_from loc_to - location
 )
 (:predicates
 (at_ ?object - object_ ?location - location)
  (in ?package - package ?vehicle - vehicle)
  (:private
   (a_pos ?agent - airplane_type ?location - location)
   (a_on ?agent - airplane_type ?object - object_)))
 (:action load_airplane
  :parameters ( ?airplane - airplane_type ?loc - airport)
  :precondition (and 
   (at_ obj ?loc)
   (a_pos ?airplane ?loc)
  )
  :effect (and
   (not (at_ obj ?loc))
   (a_on ?airplane obj)
))
 (:action unload_airplane
  :parameters ( ?airplane - airplane_type ?loc - airport)
  :precondition (and 
   (a_on ?airplane obj)
   (a_pos ?airplane ?loc)
  )
  :effect (and
   (not (a_on ?airplane obj))
   (at_ obj ?loc)
))
 (:action fly_airplane
  :parameters ( ?airplane - airplane_type)
  :precondition (and 
   (a_pos ?airplane loc_from)
  )
  :effect (and
   (not (a_pos ?airplane loc_from))
   (a_pos ?airplane loc_to)
))
)
