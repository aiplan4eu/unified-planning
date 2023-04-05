(define (domain ma_logistic-domain)
 (:requirements :factored-privacy :typing)
 (:types
    object_ driver1_type driver2_type driver3_type - object
    location city vehicle package - object_
    truck airplane - vehicle
    airport - location
 )
 (:constants
   obj - package
   airplane_ - airplane
   loc_from loc_to - location
 )
 (:predicates
 (at_ ?object - object_ ?location - location)
  (on ?object - object_)
  (in ?package - package ?vehicle - vehicle)
  (:private
   (a_pos ?agent - driver3_type ?location - location)
   (a_driving_p ?agent - driver3_type ?airplane - airplane)))
 (:action load_airplane
  :parameters ( ?driver3 - driver3_type ?loc - airport)
  :precondition (and 
   (at_ obj ?loc)
   (at_ airplane_ ?loc)
   (a_pos ?driver3 ?loc)
  )
  :effect (and
   (not (at_ obj ?loc))
   (in obj airplane_)
))
 (:action unload_airplane
  :parameters ( ?driver3 - driver3_type ?loc - airport)
  :precondition (and 
   (in obj airplane_)
   (at_ airplane_ ?loc)
   (a_pos ?driver3 ?loc)
  )
  :effect (and
   (not (in obj airplane_))
   (at_ obj ?loc)
))
 (:action fly_airplane
  :parameters ( ?driver3 - driver3_type)
  :precondition (and 
   (at_ airplane_ loc_from)
   (a_pos ?driver3 loc_from)
   (a_driving_p ?driver3 airplane_)
  )
  :effect (and
   (not (at_ airplane_ loc_from))
   (at_ airplane_ loc_to)
   (a_pos ?driver3 loc_to)
))
)
