(define (domain ma_taxi-domain)
 (:requirements :factored-privacy :typing)
 (:types location taxi ag - object
    person1_type person2_type driver1_type driver2_type - ag
 )
 (:predicates
  (free ?location - location)
  (directly_connected ?l1 - location ?l2 - location)
  (at_ ?taxi - taxi ?location - location)
  (empty ?taxi - taxi)
  (a_pos ?agent - ag ?location - location)
  (a_in ?agent - ag ?taxi - taxi)
  (:private
   (a_driving ?agent - ag ?taxi - taxi)))
 (:action drive_t
  :parameters ( ?driver1 - driver1_type ?t - taxi ?from_ - location ?to - location)
  :precondition (and 
   (a_driving ?driver1 ?t)
   (at_ ?t ?from_)
   (directly_connected ?from_ ?to)
   (free ?to)
  )
  :effect (and
   (not (at_ ?t ?from_))
   (not (free ?to))
   (at_ ?t ?to)
   (free ?from_)
))
)
